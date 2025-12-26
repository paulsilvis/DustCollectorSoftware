from __future__ import annotations
import logging

from .i2c_bus import I2CBus
from .pcf8574 import PCF8574
from .uart import open_serial

log = logging.getLogger("hardware")


class Hardware:
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

    def pcf_write_init(self):
        # Idle high everywhere on outputs
        self.pcf_led.write_byte(0xFF)
        self.pcf_act.write_byte(0xFF)

    def gpio_set_ssr(self, gpio, on: bool):
        gpio.write(on)

    def serial_write_line(self, line: str) -> None:
        self.serial.write((line.strip() + "\n").encode("utf-8"))

    def led_set_pair(self, red_bit: int, green_bit: int, *, red_on: bool, green_on: bool):
        # active-low sink: 0 = ON, 1 = OFF
        state = self.pcf_led.state

        def setbit(st: int, b: int, on: bool) -> int:
            return (st & ~(1 << b)) if on else (st | (1 << b))

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

    def relays_stop_gate(self, fwd_bit: int, rev_bit: int):
        # Idle both relays high (active-low board)
        self._pcf_act_update(set_mask=(1 << fwd_bit) | (1 << rev_bit))

    def relays_drive(self, bit: int, active_low_on: bool):
        if active_low_on:
            self._pcf_act_update(clear_mask=(1 << bit))
        else:
            self._pcf_act_update(set_mask=(1 << bit))
