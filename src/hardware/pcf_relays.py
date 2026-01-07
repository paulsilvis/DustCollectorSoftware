from __future__ import annotations

import logging
from dataclasses import dataclass

from smbus2 import SMBus

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PcfRelaysConfig:
    bus: int
    addr: int

    # IMPORTANT:
    # active_low refers to the *PCF8574 output pin polarity*:
    # - active_low=True  => PCF drives LOW to energize (bit=0 means ON)
    # - active_low=False => PCF drives HIGH to energize (bit=1 means ON)
    #
    # Your proven wiring for relays is:
    #   PCF -> ULN2803 (inverts) -> relay inputs (active-low jumper)
    # Therefore the effective PCF polarity is ACTIVE-HIGH => active_low=False.
    active_low: bool = True


class PcfRelays:
    """
    Controls relay inputs via a PCF8574-style expander.

    Notes:
    - This is a *byte* device: writes replace all 8 outputs.
    - We do read-modify-write and touch only the specified bits.
    - active_low is defined at the PCF output pin (see PcfRelaysConfig).
    - We capture the original byte on init so we can restore it (optional).
    """

    def __init__(self, cfg: PcfRelaysConfig) -> None:
        self._cfg = cfg
        self._bus = SMBus(cfg.bus)

        self._orig = self._read_byte()
        self._cur = self._orig

        log.info(
            "PCF relays init: bus=%s addr=0x%02x active_low=%s orig=0x%02x",
            cfg.bus,
            cfg.addr,
            cfg.active_low,
            self._orig,
        )

    def close(self, *, restore: bool = True) -> None:
        if restore:
            try:
                self._write_byte(self._orig)
            except Exception:
                log.exception("Failed to restore PCF relay byte")
        try:
            self._bus.close()
        except Exception:
            pass

    def set_relay(self, bit: int, on: bool) -> None:
        base = self._read_byte()
        v = self._set_bit(base, bit, on)
        self._write_byte(v)
        self._cur = v

    def stop_pair(self, bit_a: int, bit_b: int) -> None:
        base = self._read_byte()
        v = base
        v = self._set_bit(v, bit_a, False)
        v = self._set_bit(v, bit_b, False)
        self._write_byte(v)
        self._cur = v

    def all_off(self) -> None:
        # For PCF-active-low: OFF = HIGH => 0xFF
        # For PCF-active-high: OFF = LOW  => 0x00  (matches your openclose.py)
        off = 0xFF if self._cfg.active_low else 0x00
        self._write_byte(off)
        self._cur = off

    # -------- internals --------

    def _mask(self, bit: int) -> int:
        return 1 << bit

    def _set_bit(self, byte_val: int, bit: int, on: bool) -> int:
        # If PCF is active_low:
        #   on=True  -> drive LOW  -> bit=0
        #   on=False -> drive HIGH -> bit=1
        # If PCF is active_high:
        #   on=True  -> drive HIGH -> bit=1
        #   on=False -> drive LOW  -> bit=0
        drive_high = (not on) if self._cfg.active_low else on
        return (
            (byte_val | self._mask(bit))
            if drive_high
            else (byte_val & ~self._mask(bit))
        )

    def _read_byte(self) -> int:
        return int(self._bus.read_byte(self._cfg.addr))

    def _write_byte(self, value: int) -> None:
        self._bus.write_byte(self._cfg.addr, value & 0xFF)
