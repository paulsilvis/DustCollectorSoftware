from __future__ import annotations

from .typing import IntEnumLike  # optional helper, see below
from ..hardware.leds_hw import LedBank


class Leds:
    """
    Named LED signals on the LED PCF.

    This layer knows:
      - which bit index corresponds to which semantic name
    It does NOT impose relationships like "pairs must be mutually exclusive";
    that is policy for tasks.
    """

    # Bit assignments (adjust to match your wiring)
    SAW_ON = 0
    SAW_OFF = 1
    LATHE_ON = 2
    LATHE_OFF = 3
    DRILL_ON = 4
    DRILL_OFF = 5
    SPARE_ON = 6
    SPARE_OFF = 7

    def __init__(self, bank: LedBank) -> None:
        self._bank = bank

    async def on(self, bit: int) -> None:
        await self._bank.set_bit(bit, True)

    async def off(self, bit: int) -> None:
        await self._bank.set_bit(bit, False)

    async def all_on(self) -> None:
        await self._bank.all_on()

    async def all_off(self) -> None:
        await self._bank.all_off()
