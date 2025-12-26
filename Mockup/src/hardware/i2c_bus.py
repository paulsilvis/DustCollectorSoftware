from __future__ import annotations
import smbus2


class I2CBus:
    def __init__(self, bus_id: int = 1) -> None:
        self.bus = smbus2.SMBus(bus_id)
