from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from ..events import Event
from ..event_bus import EventBus

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdcWatchConfig:
    i2c_address: int = 0x48

    # Quiet, responsive enough
    sample_hz: float = 10.0

    # Lathe mapping
    lathe_channel: int = 1  # A1

    # FINAL thresholds (VOLTS at ADC input)
    lathe_on_threshold: float = 0.040
    lathe_off_threshold: float = 0.025

    # Stability against noise
    consecutive_required: int = 3


async def run_adc_watch(cfg: AdcWatchConfig, bus: EventBus) -> None:
    """
    Quiet ADS1115 lathe detector with hysteresis.

    Publishes ONLY on OFF->ON and ON->OFF transitions:
      - Event type: "lathe.on" / "lathe.off"
      - src: "adc.a1"
      - data: {"v": <voltage>}
    """
    import board  # type: ignore
    import busio  # type: ignore
    import adafruit_ads1x15.ads1115 as ADS  # type: ignore
    from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore

    if cfg.sample_hz <= 0:
        raise ValueError("sample_hz must be > 0")
    if cfg.consecutive_required < 1:
        raise ValueError("consecutive_required must be >= 1")
    if cfg.lathe_channel != 1:
        raise ValueError("This watcher expects lathe_channel=1 (A1)")

    period = 1.0 / cfg.sample_hz

    log.info(
        "ADC lathe watch start: addr=0x%02x sample_hz=%.1f "
        "ON=%.3fV OFF=%.3fV consec=%d",
        cfg.i2c_address,
        cfg.sample_hz,
        cfg.lathe_on_threshold,
        cfg.lathe_off_threshold,
        cfg.consecutive_required,
    )

    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=cfg.i2c_address)
    lathe = AnalogIn(ads, ADS.P1)

    lathe_on = False
    above_on = 0
    below_off = 0

    try:
        while True:
            v = float(lathe.voltage)

            if not lathe_on:
                if v >= cfg.lathe_on_threshold:
                    above_on += 1
                    if above_on >= cfg.consecutive_required:
                        lathe_on = True
                        above_on = 0
                        below_off = 0
                        await bus.publish(Event.now("lathe.on", "adc.a1", v=v))
                else:
                    above_on = 0
            else:
                if v <= cfg.lathe_off_threshold:
                    below_off += 1
                    if below_off >= cfg.consecutive_required:
                        lathe_on = False
                        above_on = 0
                        below_off = 0
                        await bus.publish(Event.now("lathe.off", "adc.a1", v=v))
                else:
                    below_off = 0

            await asyncio.sleep(period)

    except asyncio.CancelledError:
        log.info("ADC lathe watch cancelled")
        raise
