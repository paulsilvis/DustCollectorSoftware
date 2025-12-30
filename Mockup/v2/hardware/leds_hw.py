from __future__ import annotations

from .pcf8574 import Pcf8574


class LedBank:
    """
    Active-high LED outputs via PCF8574.

    At this level, we do *not* know about SAW/LATHE/etc.,
    only about bits 0..7 being ON or OFF.
    """

    def __init__(self, pcf: Pcf8574) -> None:
        self._pcf = pcf

    async def set_bits(self, mask: int, on_mask: int) -> None:
        """
        Turn on/off multiple LEDs at once.

        mask: which bits are affected
        on_mask: which of those should be ON (1) vs OFF (0)
        """
        mask &= 0xFF
        on_mask &= mask
        await self._pcf.update_bits(mask, on_mask)

    async def set_bit(self, bit: int, on: bool) -> None:
        if not 0 <= bit <= 7:
            raise ValueError(f"LED bit out of range: {bit}")
        mask = 1 << bit
        await self.set_bits(mask, mask if on else 0)

    async def all_on(self) -> None:
        await self._pcf.write_byte(0xFF)

    async def all_off(self) -> None:
        await self._pcf.write_byte(0x00)

