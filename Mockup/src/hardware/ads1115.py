from __future__ import annotations
import logging

log = logging.getLogger("ads1115")


class ADS1115Reader:
    """Thin wrapper around Adafruit ADS1115 driver.

    Lazy-imports hardware-only modules so this file is importable on laptops.
    In mock mode, adc_watch does not instantiate this class.
    """

    def __init__(self, addr: int = 0x48, sps: int = 128):
        try:
            import board
            import busio
            import adafruit_ads1x15.ads1115 as ADS
            from adafruit_ads1x15.analog_in import AnalogIn
        except Exception as e:  # pragma: no cover
            raise RuntimeError(
                "ADS1115 libs not available. On the Pi, install "
                "`adafruit-circuitpython-ads1x15` and enable I2C. "
                "On a laptop, set `system.mock: true`."
            ) from e

        i2c = busio.I2C(board.SCL, board.SDA)
        self.ads = ADS.ADS1115(i2c, address=addr)
        self.ads.gain = 1          # ±4.096 V
        self.ads.data_rate = sps
        self._channels = [
            AnalogIn(self.ads, ADS.P0),
            AnalogIn(self.ads, ADS.P1),
            AnalogIn(self.ads, ADS.P2),
            AnalogIn(self.ads, ADS.P3),
        ]

    def read_volts(self, ch: int) -> float:
        return float(self._channels[ch].voltage)
