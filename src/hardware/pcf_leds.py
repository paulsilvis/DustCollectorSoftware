from __future__ import annotations

import logging
from dataclasses import dataclass

from smbus2 import SMBus

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class PcfLedsConfig:
    bus: int
    addr: int
    green_bit: int
    red_bit: int
    active_low: bool = True


class PcfLedPair:
    """
    Controls a RED/GREEN LED pair driven by a PCF8574-style expander.

    Safety:
    - PCF writes a whole byte.
    - We always do read-modify-write.
    - Only configured bits are touched.
    """

    def __init__(self, cfg: PcfLedsConfig) -> None:
        self._cfg = cfg
        self._bus = SMBus(cfg.bus)

        self._orig = self._read_byte()
        self._cur = self._orig

        log.info(
            "PCF LED pair init: bus=%s addr=0x%02x green=%s red=%s active_low=%s orig=0x%02x",
            cfg.bus,
            cfg.addr,
            cfg.green_bit,
            cfg.red_bit,
            cfg.active_low,
            self._orig,
        )

    def close(self, *, restore: bool = True) -> None:
        if restore:
            try:
                self._write_byte(self._orig)
            except Exception:
                log.exception("Failed to restore PCF byte")
        try:
            self._bus.close()
        except Exception:
            pass

    def set_green(self) -> None:
        self._set(red_on=False, green_on=True)

    def set_red(self) -> None:
        self._set(red_on=True, green_on=False)

    def set_off(self) -> None:
        self._set(red_on=False, green_on=False)

    # -------- internals --------

    def _mask(self, bit: int) -> int:
        return 1 << bit

    def _set_bit(self, byte_val: int, bit: int, on: bool) -> int:
        drive_high = (not on) if self._cfg.active_low else on
        return (byte_val | self._mask(bit)) if drive_high else (byte_val & ~self._mask(bit))

    def _set(self, *, red_on: bool, green_on: bool) -> None:
        base = self._read_byte()
        v = base
        v = self._set_bit(v, self._cfg.green_bit, green_on)
        v = self._set_bit(v, self._cfg.red_bit, red_on)
        self._write_byte(v)
        self._cur = v

    def _read_byte(self) -> int:
        return int(self._bus.read_byte(self._cfg.addr))

    def _write_byte(self, value: int) -> None:
        self._bus.write_byte(self._cfg.addr, value & 0xFF)
