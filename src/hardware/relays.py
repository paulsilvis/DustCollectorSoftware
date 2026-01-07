from __future__ import annotations
from dataclasses import dataclass

from .pcf8574 import PCF8574
import time
import logging

log = logging.getLogger("relays")


@dataclass
class HBridgeMap:
    fwd_bit: int
    rev_bit: int


class ActuatorRelays:
    def __init__(self, pcf: "PCF8574", dead_time_ms: int = 200):
        self.pcf = pcf
        self.dead_time_ms = dead_time_ms

    def _bit(self, b: int, val: int) -> int:
        mask = 1 << b
        if val:
            return int(self.pcf.state | mask)
        return int(self.pcf.state & ~mask)

    def set_bits(self, changes: dict[int, int]):
        state = self.pcf.state
        for b, v in changes.items():
            state = (state | (1 << b)) if v else (state & ~(1 << b))
        self.pcf.write_byte(state)

    def stop(self, m: HBridgeMap):
        # active-low relays, so "1" = idle
        self.set_bits({m.fwd_bit: 1, m.rev_bit: 1})

    def forward(self, m: HBridgeMap):
        # enforce no overlap
        self.set_bits({m.rev_bit: 1})
        time.sleep(self.dead_time_ms / 1000)
        self.set_bits({m.fwd_bit: 0})

    def reverse(self, m: HBridgeMap):
        self.set_bits({m.fwd_bit: 1})
        time.sleep(self.dead_time_ms / 1000)
        self.set_bits({m.rev_bit: 0})

