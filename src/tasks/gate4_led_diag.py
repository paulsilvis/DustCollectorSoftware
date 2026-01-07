"""
Gate 4 LED diagnostic blinker via PCF8574 (I2C).

Known-good mapping (per Paul's shop test):
- PCF address: 0x20
- GREEN: bit 3
- RED: bit 7
- Polarity: ACTIVE-LOW (0 = LED ON, 1 = LED OFF)

Safety:
- PCF8574 writes a whole byte. We do a read-modify-write that only touches the
  LED bits and we restore the original byte on exit/cancel.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from smbus2 import SMBus

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PcfLedMapping:
    bus: int
    addr: int
    green_bit: int
    red_bit: int
    active_low: bool = True


def _mask(bit: int) -> int:
    if bit < 0 or bit > 7:
        raise ValueError(f"bit must be 0..7, got {bit}")
    return 1 << bit


def _set_led_bit(byte_val: int, bit: int, on: bool, active_low: bool) -> int:
    """
    Return a modified byte with only `bit` adjusted to logical state `on`.
    """
    m = _mask(bit)

    # active-high: ON -> 1, OFF -> 0
    # active-low : ON -> 0, OFF -> 1
    drive_high = (not on) if active_low else on

    if drive_high:
        return byte_val | m
    return byte_val & ~m


async def run_gate4_led_diag(
    mapping: PcfLedMapping,
    *,
    on_sec: float = 1.0,
    gap_sec: float = 0.2,
    rest_sec: float = 0.8,
) -> None:
    """
    Blink pattern (cannot be mistaken for a real gate state):
      GREEN on (1.0s), off (0.2s), RED on (1.0s), off (0.8s), repeat
    """
    log.info(
        "Gate4 LED diag start: i2c_bus=%s addr=0x%02x green_bit=%s red_bit=%s "
        "active_low=%s",
        mapping.bus,
        mapping.addr,
        mapping.green_bit,
        mapping.red_bit,
        mapping.active_low,
    )

    bus = SMBus(mapping.bus)
    try:
        orig = bus.read_byte(mapping.addr)
        cur = orig

        # Start with both OFF (logical OFF)
        cur = _set_led_bit(cur, mapping.green_bit, on=False, active_low=mapping.active_low)
        cur = _set_led_bit(cur, mapping.red_bit, on=False, active_low=mapping.active_low)
        bus.write_byte(mapping.addr, cur)

        while True:
            # GREEN on
            cur = _set_led_bit(cur, mapping.green_bit, on=True, active_low=mapping.active_low)
            bus.write_byte(mapping.addr, cur)
            await asyncio.sleep(on_sec)

            # GREEN off
            cur = _set_led_bit(cur, mapping.green_bit, on=False, active_low=mapping.active_low)
            bus.write_byte(mapping.addr, cur)
            await asyncio.sleep(gap_sec)

            # RED on
            cur = _set_led_bit(cur, mapping.red_bit, on=True, active_low=mapping.active_low)
            bus.write_byte(mapping.addr, cur)
            await asyncio.sleep(on_sec)

            # RED off
            cur = _set_led_bit(cur, mapping.red_bit, on=False, active_low=mapping.active_low)
            bus.write_byte(mapping.addr, cur)
            await asyncio.sleep(rest_sec)

    except asyncio.CancelledError:
        log.info("Gate4 LED diag cancelled; restoring PCF byte")
        raise
    finally:
        try:
            # Restore original latch state no matter what.
            bus.write_byte(mapping.addr, orig)
        except Exception:
            log.exception("Failed restoring PCF original byte on shutdown")
        try:
            bus.close()
        except Exception:
            pass
