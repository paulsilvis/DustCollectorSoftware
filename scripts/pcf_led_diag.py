#!/usr/bin/env python3
"""
PCF8574 LED diagnostic blink (safe read-modify-write).

Defaults:
- I2C bus: 1
- PCF address: 0x20
- RED bit: 6
- GREEN bit: 7

IMPORTANT:
- PCF8574 writes a full byte. We read current state and only touch the two
  selected bits, then restore the original byte on exit.
- Many PCF8574 LED hookups are ACTIVE-LOW (writing 0 sinks current = LED ON).
  Use --active-low if your LEDs are wired that way.
"""

from __future__ import annotations

import argparse
import time
from dataclasses import dataclass

from smbus2 import SMBus


@dataclass(frozen=True)
class LedBits:
    red: int
    green: int


def _mask(bit: int) -> int:
    if bit < 0 or bit > 7:
        raise ValueError(f"bit must be 0..7, got {bit}")
    return 1 << bit


def _set_led(byte_val: int, bit: int, on: bool, active_low: bool) -> int:
    """
    Return new byte with only 'bit' altered according to desired logical state.
    """
    m = _mask(bit)

    # For active-high: ON => 1, OFF => 0
    # For active-low : ON => 0, OFF => 1
    if active_low:
        drive_high = not on
    else:
        drive_high = on

    if drive_high:
        return byte_val | m
    return byte_val & ~m


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--bus", type=int, default=1)
    ap.add_argument("--addr", type=lambda s: int(s, 0), default=0x20)
    ap.add_argument("--red-bit", type=int, default=6)
    ap.add_argument("--green-bit", type=int, default=7)
    ap.add_argument("--active-low", action="store_true")
    ap.add_argument("--cycles", type=int, default=20)
    ap.add_argument("--on-sec", type=float, default=1.0)
    ap.add_argument("--gap-sec", type=float, default=0.2)
    ap.add_argument("--rest-sec", type=float, default=0.8)
    args = ap.parse_args()

    bits = LedBits(red=args.red_bit, green=args.green_bit)

    print("== PCF LED diagnostic ==")
    print(f"bus={args.bus} addr=0x{args.addr:02x} red_bit={bits.red} green_bit={bits.green}")
    print(f"active_low={args.active_low} cycles={args.cycles}")
    print("Pattern: GREEN on, gap, RED on, rest (repeat)")
    print()

    with SMBus(args.bus) as bus:
        orig = bus.read_byte(args.addr)
        cur = orig
        print(f"orig_byte=0b{orig:08b} (0x{orig:02x})")

        try:
            # Start with both OFF (logical OFF)
            cur = _set_led(cur, bits.red, on=False, active_low=args.active_low)
            cur = _set_led(cur, bits.green, on=False, active_low=args.active_low)
            bus.write_byte(args.addr, cur)

            for _ in range(args.cycles):
                # GREEN on
                cur = _set_led(cur, bits.green, on=True, active_low=args.active_low)
                bus.write_byte(args.addr, cur)
                time.sleep(args.on_sec)

                # GREEN off
                cur = _set_led(cur, bits.green, on=False, active_low=args.active_low)
                bus.write_byte(args.addr, cur)
                time.sleep(args.gap_sec)

                # RED on
                cur = _set_led(cur, bits.red, on=True, active_low=args.active_low)
                bus.write_byte(args.addr, cur)
                time.sleep(args.on_sec)

                # RED off
                cur = _set_led(cur, bits.red, on=False, active_low=args.active_low)
                bus.write_byte(args.addr, cur)
                time.sleep(args.rest_sec)

        finally:
            bus.write_byte(args.addr, orig)
            print(f"restored_byte=0b{orig:08b} (0x{orig:02x})")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())

