#!/usr/bin/env python3
import time
from smbus2 import SMBus

ADDR = 0x20
BUS = 1

def w(bus, v):
    bus.write_byte(ADDR, v & 0xFF)

def r(bus):
    return bus.read_byte(ADDR)

with SMBus(BUS) as bus:
    print(f"PCF@0x{ADDR:02x} initial read: 0x{r(bus):02x}")

    # Start from all-high
    w(bus, 0xFF)
    time.sleep(1.0)

    # Walk one bit low at a time
    for b in range(8):
        v = 0xFF & ~(1 << b)
        print(f"bit {b} LOW: write 0x{v:02x}")
        w(bus, v)
        time.sleep(1.0)

    # Walk one bit high at a time from all-low
    w(bus, 0x00)
    time.sleep(1.0)
    for b in range(8):
        v = (1 << b)
        print(f"bit {b} HIGH only: write 0x{v:02x}")
        w(bus, v)
        time.sleep(1.0)

    # Restore to all-high
    w(bus, 0xFF)
    print("done; restored 0xFF")
