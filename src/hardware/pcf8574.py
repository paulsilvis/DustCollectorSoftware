from __future__ import annotations
import time


class PCF8574:
    def __init__(self, i2c, addr: int):
        self.i2c = i2c
        self.addr = addr
        self.state = 0xFF  # high (idle) on power-up

    def write_byte(self, value: int) -> None:
        value &= 0xFF
        self.state = value
        self.i2c.bus.write_byte(self.addr, value)

    def read_byte(self) -> int:
        return int(self.i2c.bus.read_byte(self.addr))
