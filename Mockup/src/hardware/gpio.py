from __future__ import annotations

from dataclasses import dataclass
from typing import Any


try:
    import RPi.GPIO as _GPIO
except Exception:  # pragma: no cover
    _GPIO = None


@dataclass
class GPIOOut:
    pin: int
    active_high: bool = True
    _initialized: bool = False

    def _init(self) -> None:
        if self._initialized:
            return
        if _GPIO is None:
            raise RuntimeError("RPi.GPIO not available on this platform")
        _GPIO.setmode(_GPIO.BCM)
        _GPIO.setup(self.pin, _GPIO.OUT)
        self._initialized = True

    def write(self, on: bool) -> None:
        self._init()
        assert _GPIO is not None
        level = _GPIO.HIGH if (on if self.active_high else not on) else _GPIO.LOW
        _GPIO.output(self.pin, level)

    def on(self) -> None:
        self.write(True)

    def off(self) -> None:
        self.write(False)
