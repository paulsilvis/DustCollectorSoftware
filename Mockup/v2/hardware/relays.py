from __future__ import annotations

from dataclasses import dataclass

from .pcf8574 import Pcf8574


@dataclass(frozen=True)
class RelayBankConfig:
    """
    Configuration for the relay bank.

    effective_active_low explains the net polarity as seen at the PCF8574:
    - True  => writing 0 energizes the relay (PCF bit=0 => ON)
    - False => writing 1 energizes the relay (PCF bit=1 => ON)

    For your wiring:
      PCF -> ULN2803 (inverts) -> relay inputs (jumpered active-low)

    That typically means:
        PCF bit = 1  -> ULN in=1 -> ULN out≈0 -> relay "active" because
                             relay board treats 0 as ON
    But because there are jumpers and previous confusion, we keep this
    explicit and configurable.
    """

    effective_active_low: bool = True


class RelayBank:
    """
    Byte-based relay controller.

    At this level:
      - "logical ON" means "energize this relay"
      - "logical OFF" means "de-energize this relay"

    Mapping to PCF bits is handled by effective_active_low.
    """

    def __init__(self, pcf: Pcf8574, cfg: RelayBankConfig | None = None) -> None:
        self._pcf = pcf
        self._cfg = cfg or RelayBankConfig()

    def _to_pcf_bits(self, mask: int, logical_on_mask: int) -> int:
        """
        Map logical ON/OFF bits to PCF bit values under effective_active_low.
        """
        logical_on_mask &= mask

        if self._cfg.effective_active_low:
            # ON  => drive low  (0)
            # OFF => drive high (1)
            return (~logical_on_mask) & mask
        else:
            # ON  => drive high (1)
            # OFF => drive low  (0)
            return logical_on_mask & mask

    async def set_bits(self, mask: int, logical_on_mask: int) -> None:
        """
        Set/clear multiple relays in one atomic update.

        mask: which relays we are touching
        logical_on_mask: which of those should be ON
        """
        mask &= 0xFF
        pcf_bits = self._to_pcf_bits(mask, logical_on_mask)
        await self._pcf.update_bits(mask, pcf_bits)

    async def set_bit(self, bit: int, on: bool) -> None:
        mask = 1 << bit
        logical = mask if on else 0
        await self.set_bits(mask, logical)
