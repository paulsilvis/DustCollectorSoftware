from dataclasses import dataclass
from typing import Dict
import time


@dataclass
class Event:
    type: str      # e.g. "machine.on", "machine.off", "system.any_active"
    src: str       # e.g. "adc.tablesaw"
    ts: float
    data: Dict

    @staticmethod
    def now(type_: str, src: str, **data):
        return Event(type=type_, src=src, ts=time.monotonic(), data=data)
