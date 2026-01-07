from __future__ import annotations

import logging

log = logging.getLogger("mock_hw")


class MockSerial:
    def read(self, n: int) -> bytes:
        return b""

    def write(self, data: bytes) -> int:
        try:
            txt = data.decode("utf-8", errors="replace").strip()
        except Exception:
            txt = repr(data)
        log.info("ESP32 TX: %s", txt)
        return len(data)


class MockPCF8574:
    def __init__(self, addr: int):
        self.addr = addr
        self.state = 0xFF

    def write_byte(self, value: int) -> None:
        value &= 0xFF
        self.state = value
        log.info("PCF8574 0x%02X <= 0x%02X", self.addr, value)


class MockGPIOOut:
    def __init__(self, pin: int, active_high: bool = True):
        self.pin = pin
        self.active_high = active_high
        self.state = False

    def write(self, on: bool) -> None:
        self.state = bool(on)
        level = "HIGH" if (on if self.active_high else not on) else "LOW"
        log.info(
            "GPIO%d SSR => %s (level=%s)",
            self.pin,
            "ON" if on else "OFF",
            level,
        )

    def on(self) -> None:
        self.write(True)

    def off(self) -> None:
        self.write(False)


class MockHardware:
    """
    Mock hardware implementation with the same surface API as Hardware.
    """

    def __init__(self, cfg):
        self.cfg = cfg
        self.pcf_led = MockPCF8574(cfg.raw["i2c"]["pcf_led_addr"])
        self.pcf_act = MockPCF8574(cfg.raw["i2c"]["pcf_act_addr"])
        self.serial = MockSerial()
        self.ser_tx = self.serial  # legacy name used by funhouse

        # Commonly-used SSR pins (existing code references these)
        self.gpio25 = MockGPIOOut(25)
        self.gpio24 = MockGPIOOut(24)

    def pcf_write_init(self) -> None:
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
        state = self.pcf_led.state

        def setbit(st: int, b: int, on_: bool) -> int:
            return (st & ~(1 << b)) if on_ else (st | (1 << b))

        state = setbit(state, red_bit, red_on)
        state = setbit(state, green_bit, green_on)
        self.pcf_led.write_byte(state)

    # ---- Relay-bank helpers (atomic masked updates) ----
    def _pcf_act_update(self, *, set_mask: int = 0, clear_mask: int = 0) -> None:
        new_state = (self.pcf_act.state | (set_mask & 0xFF)) & ~(clear_mask & 0xFF)
        self.pcf_act.write_byte(new_state)

    def relays_stop_gate(self, fwd_bit: int, rev_bit: int) -> None:
        self._pcf_act_update(set_mask=(1 << fwd_bit) | (1 << rev_bit))

    def relays_drive(self, bit: int, active_low_on: bool) -> None:
        if active_low_on:
            self._pcf_act_update(clear_mask=(1 << bit))
        else:
            self._pcf_act_update(set_mask=(1 << bit))
