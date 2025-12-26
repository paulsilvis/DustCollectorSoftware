from __future__ import annotations

import logging
import os
from typing import Literal, Optional

from .gpio import GPIOOut
from .i2c_bus import I2CBus
from .pcf8574 import PCF8574
from .uart import open_serial

log = logging.getLogger("hardware")

HardwareMode = Literal["mock", "real"]


def _normalize_mode(s: Optional[str]) -> Optional[HardwareMode]:
    if s is None:
        return None
    val = s.strip().lower()
    if val in ("mock", "real"):
        return val  # type: ignore[return-value]
    return None


def _cfg_hw_mode(cfg) -> HardwareMode:
    raw = getattr(cfg, "raw", {}) or {}
    hw = raw.get("hardware", {}) or {}
    mode = _normalize_mode(hw.get("mode"))
    return mode or "mock"


def _env_hw_mode() -> Optional[HardwareMode]:
    return _normalize_mode(os.environ.get("DUSTCOLLECTOR_HW"))


def _cfg_outputs_enabled(cfg) -> bool:
    raw = getattr(cfg, "raw", {}) or {}
    hw = raw.get("hardware", {}) or {}
    # Default: False (safety)
    return bool(hw.get("outputs_enabled", False))


def get_hardware(cfg):
    """
    Single, centralized selector for mock vs real hardware.
    """
    mode_env = _env_hw_mode()
    mode_cfg = _cfg_hw_mode(cfg)

    if mode_env is not None:
        mode = mode_env
        source = "env:DUSTCOLLECTOR_HW"
    else:
        mode = mode_cfg
        source = "config:hardware.mode (default=mock)"

    log.warning("HW mode = %s (selected via %s)", mode, source)

    if mode == "mock":
        from .mock_hw import MockHardware
        return MockHardware(cfg)

    return Hardware(cfg)


class Hardware:
    """
    Real hardware implementation.

    Safety:
    - outputs_enabled defaults to False
    - when inhibited, output methods log and do nothing
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.outputs_enabled = _cfg_outputs_enabled(cfg)

        # I2C + expanders
        self.i2c = I2CBus(cfg.raw["i2c"]["bus"])
        self.pcf_led = PCF8574(self.i2c, cfg.raw["i2c"]["pcf_led_addr"])
        self.pcf_act = PCF8574(self.i2c, cfg.raw["i2c"]["pcf_act_addr"])
        self.pcf_spares = [
            PCF8574(self.i2c, addr)
            for addr in cfg.raw["i2c"]["pcf_spare_addrs"]
        ]

        # UART
        self.serial = open_serial(
            cfg.raw["uart"]["port"],
            cfg.raw["uart"]["baud"],
        )
        self.ser_tx = self.serial  # legacy alias

        # GPIO SSR outputs (BCM numbering)
        collector_pin = int(cfg.raw["gpio"]["collector_ssr"])
        fan_pin = int(cfg.raw["gpio"]["fan_ssr"])
        self.gpio25 = GPIOOut(collector_pin, active_high=True)
        self.gpio24 = GPIOOut(fan_pin, active_high=True)

        log.warning(
            "HW outputs_enabled=%s (set hardware.outputs_enabled=true to energize outputs)",
            self.outputs_enabled,
        )

    # ---------------- Safety gate ----------------

    def _inhibited(self, what: str) -> bool:
        if self.outputs_enabled:
            return False
        log.warning("OUTPUT INHIBITED: %s", what)
        return True

    # ---------------- Public API ----------------

    def pcf_write_init(self) -> None:
        if self._inhibited("pcf_write_init()"):
            return
        self.pcf_led.write_byte(0xFF)
        self.pcf_act.write_byte(0xFF)

    def gpio_set_ssr(self, gpio, on: bool) -> None:
        if self._inhibited(
            f"gpio_set_ssr(pin={getattr(gpio, 'pin', '?')}, on={on})"
        ):
            return
        gpio.write(on)

    def serial_write_line(self, line: str) -> None:
        # Serial TX is non-dangerous; allow even when outputs inhibited
        self.serial.write((line.strip() + "\n").encode("utf-8"))

    def led_set_pair(
        self,
        red_bit: int,
        green_bit: int,
        *,
        red_on: bool,
        green_on: bool,
    ) -> None:
        if self._inhibited(
            f"led_set_pair(r={red_bit}, g={green_bit}, "
            f"red_on={red_on}, green_on={green_on})"
        ):
            return

        state = self.pcf_led.state

        def setbit(st: int, b: int, on_: bool) -> int:
            return (st & ~(1 << b)) if on_ else (st | (1 << b))

        state = setbit(state, red_bit, red_on)
        state = setbit(state, green_bit, green_on)
        self.pcf_led.write_byte(state)

    # ---- Relay-bank helpers (atomic masked updates) ----

    def _pcf_act_update(self, *, set_mask: int = 0, clear_mask: int = 0) -> None:
        if self._inhibited(
            f"_pcf_act_update(set=0x{set_mask:02X}, clear=0x{clear_mask:02X})"
        ):
            return
        new_state = (self.pcf_act.state | (set_mask & 0xFF)) & ~(clear_mask & 0xFF)
        self.pcf_act.write_byte(new_state)

    def relays_stop_gate(self, fwd_bit: int, rev_bit: int) -> None:
        self._pcf_act_update(set_mask=(1 << fwd_bit) | (1 << rev_bit))

    def relays_drive(self, bit: int, active_low_on: bool) -> None:
        if active_low_on:
            self._pcf_act_update(clear_mask=(1 << bit))
        else:
            self._pcf_act_update(set_mask=(1 << bit))
