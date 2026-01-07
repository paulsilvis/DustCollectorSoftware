from __future__ import annotations
import serial


def open_serial(path: str, baud: int) -> serial.Serial:
    return serial.Serial(path, baudrate=baud, timeout=0.1)
