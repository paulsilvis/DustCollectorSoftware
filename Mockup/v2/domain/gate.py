from __future__ import annotations

from dataclasses import dataclass

from ..hardware.relays import RelayBank


@dataclass
class Gate:
    """
    One physical gate driven by two relays:

      - open_bit  : energize to open the gate
      - close_bit : energize to close the gate

    Constraint: open_bit and close_bit must never be ON at the same time.
    """

    name: str
    relay_bank: RelayBank
    open_bit: int
    close_bit: int

    async def _drive(self, open_on: bool, close_on: bool) -> None:
        if open_on and close_on:
            raise RuntimeError(f"Illegal gate drive: {self.name} open+close ON")

        mask = (1 << self.open_bit) | (1 << self.close_bit)
        logical_on = 0
        if open_on:
            logical_on |= 1 << self.open_bit
        if close_on:
            logical_on |= 1 << self.close_bit

        await self.relay_bank.set_bits(mask, logical_on)

    async def open(self) -> None:
        """Energize the 'open' direction relay."""
        await self._drive(open_on=True, close_on=False)

    async def close(self) -> None:
        """Energize the 'close' direction relay."""
        await self._drive(open_on=False, close_on=True)

    async def stop(self) -> None:
        """De-energize both relays."""
        await self._drive(open_on=False, close_on=False)
