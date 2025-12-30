from __future__ import annotations

import asyncio
from typing import Protocol

from smbus2 import SMBus


class ByteBus(Protocol):
    """
    Minimal protocol for an I2C byte-oriented device.

    This matches smbus2.SMBus for the operations we need.
    """

    def write_byte(self, addr: int, value: int) -> None:  # pragma: no cover
        ...

    def read_byte(self, addr: int) -> int:  # pragma: no cover
        ...


class Pcf8574:
    """
    Simple PCF8574 wrapper with:

    - cached state byte
    - asyncio.Lock for atomic read/modify/write
    - bitwise helpers

    This layer knows NOTHING about relays, LEDs, or polarity.
    """

    def __init__(self, bus: ByteBus, addr: int) -> None:
        self._bus: ByteBus = bus
        self._addr: int = addr
        self._lock = asyncio.Lock()
        # Power-up default is all 1s (inputs/high); we mirror that.
        self._state: int = 0xFF

    @property
    def addr(self) -> int:
        return self._addr

    async def read_byte(self) -> int:
        """
        Read the current byte from hardware and update cached state.
        """
        async with self._lock:
            value = int(self._bus.read_byte(self._addr))
            self._state = value & 0xFF
            return self._state

    async def write_byte(self, value: int) -> None:
        """
        Write an entire byte to the device and update cached state.
        """
        value &= 0xFF
        async with self._lock:
            self._bus.write_byte(self._addr, value)
            self._state = value

    async def update_bits(self, mask: int, value: int) -> None:
        """
        Atomic read/modify/write of only the bits in `mask`.

        New_state = (old_state & ~mask) | (value & mask)
        """
        mask &= 0xFF
        value &= 0xFF
        async with self._lock:
            new_state = (self._state & ~mask) | (value & mask)
            self._bus.write_byte(self._addr, new_state)
            self._state = new_state

    async def write_bit(self, bit: int, bit_val: bool) -> None:
        """
        Set or clear a single bit.
        """
        if not 0 <= bit <= 7:
            raise ValueError(f"bit out of range: {bit}")

        mask = 1 << bit
        value = mask if bit_val else 0
        await self.update_bits(mask, value)

    def cached_state(self) -> int:
        """
        Return the last known state byte (no I2C access).
        """
        return self._state


def open_default_bus(bus_id: int = 1) -> SMBus:
    """
    Convenience factory, mirroring your existing I2CBus usage.
    """
    return SMBus(bus_id)
