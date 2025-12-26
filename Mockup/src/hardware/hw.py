from __future__ import annotations

import logging
import os
from typing import Literal, Optional

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
    # Default: mock (safety)
    raw = getattr(cfg, "raw", {}) or {}
    hw = raw.get("hardware", {}) or {}
    mode = _normalize_mode(hw.get("mode"))
    return mode or "mock"


def _env_hw_mode() -> Optional[HardwareMode]:
    return _normalize_mode(os.environ.get("DUSTCOLLECTOR_HW"))


def get_hardware(cfg):
    """
    Single, centralized selector for mock vs real hardware.

    Selection precedence:
      1) env var DUSTCOLLECTOR_HW=mock|real
      2) config: hardware.mode: mock|real
      3) default: mock
    """
    mode_env = _env_hw_mode()
    mode_cfg = _cfg_hw_mode(cfg)
    mode: HardwareMode
    source: str

    if mode_env is not None:
        mode = mode_env
        source = "env:DUSTCOLLECTOR_HW"
    else:
        mode = mode_cfg
        source = "config:hardware.mode (default=mock)"

    log.warning("HW mode = %s (selected via %s)", mode, source)

    if mode == "mock":
        # Local import avoids importing mock code in real runs unless needed
        from .mock_hw import MockHardware

        return MockHardware(cfg)

    return Hardware(cfg)


class Hardware:
    """
    Real hardware implementation.

    Notes:
    - This class is intentionally thin: it wires together real drivers.
    - Safety/enable gating is handled at higher level (or via cfg later).
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.i2c = I2CBus(cfg.raw["i2c"]["bus"])
        self.pcf_led = PCF8574(self.i2c, cfg.raw["i2c"]["pcf_led_addr"])
        self.pcf_act = PCF8574(self.i2c, cfg.raw["i2c"]["pcf_act_addr"])
        self.pcf_spares = [
            PCF8574(self.i2c, a) for a in cfg.raw["i2c"]["pcf_spare_addrs"]
        ]
        self.serial = open_serial(cfg.raw["uart"]["port"], cfg.raw["uart"]["baud"])
        self.ser_tx = self.serial  # legacy name used by funhouse

    def pcf_write_init(self) -> None:
        # Idle high everywhere on outputs
        self.pcf_led.write_byte(0xFF)
        self.pcf_act.write_byte(0xFF)

    def gpio_set_ssr(self, gpio, on: bool) -> None:
        gpio.write(on)

    def serial_write_line(self, line: str) -> None:
        self.serial.write((line.strip() + "\n").encode("utf-8"))

    def led_set_pair(
        self,
        red_bit: int,
        green_bit: int,
        *,
        red_on: bool,
        green_on: bool,
    ) -> None:
        # active-low sink: 0 = ON, 1 = OFF
        state = self.pcf_led.state

        def setbit(st: int, b: int, on_: bool) -> int:
            return (st & ~(1 << b)) if on_ else (st | (1 << b))

        state = setbit(state, red_bit, red_on)
        state = setbit(state, green_bit, green_on)
        self.pcf_led.write_byte(state)

    # ---- Relay-bank helpers (atomic masked updates) ----
    def _pcf_act_update(self, *, set_mask: int = 0, clear_mask: int = 0) -> None:
        # Apply both masks to cached state and write one byte.
        # set_mask: bits forced to 1
        # clear_mask: bits forced to 0
        new_state = (self.pcf_act.state | (set_mask & 0xFF)) & ~(clear_mask & 0xFF)
        self.pcf_act.write_byte(new_state)

    def relays_stop_gate(self, fwd_bit: int, rev_bit: int) -> None:
        # Idle both relays high (active-low board)
        self._pcf_act_update(set_mask=(1 << fwd_bit) | (1 << rev_bit))

    def relays_drive(self, bit: int, active_low_on: bool) -> None:
        if active_low_on:
            self._pcf_act_update(clear_mask=(1 << bit))
        else:
            self._pcf_act_update(set_mask=(1 << bit))
