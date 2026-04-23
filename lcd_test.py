#!/usr/bin/env python3
"""Simple LCD test/utility for 4x20 I2C display at 0x3F."""

from RPLCD.i2c import CharLCD

lcd = CharLCD(
    i2c_expander='PCF8574',
    address=0x3F,
    port=1,
    cols=20,
    rows=4,
    dotsize=8,
)

lcd.clear()
lcd.write_string("Dust Collector")
lcd.cursor_pos = (1, 0)
lcd.write_string("System Ready")
lcd.cursor_pos = (2, 0)
lcd.write_string("--------------------")
lcd.cursor_pos = (3, 0)
lcd.write_string("LCD OK")
