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
    sample_hz: float = 10.0

    # Channels
    saw_channel: int = 0  # A0
    lathe_channel: int = 1  # A1

    # Thresholds (VOLTS at ADC input)
    saw_on_threshold: float = 1.00
    saw_off_threshold: float = 0.30
    lathe_on_threshold: float = 0.040
    lathe_off_threshold: float = 0.025

    # Stability against noise
    consecutive_required: int = 3


async def _watch_one(
    *,
    bus: EventBus,
    period: float,
    analog_in,
    tool: str,
    src: str,
    on_threshold: float,
    off_threshold: float,
    consecutive_required: int,
) -> None:
    is_on = False
    above_on = 0
    below_off = 0

    while True:
        v = float(analog_in.voltage)

        if not is_on:
            if v >= on_threshold:
                above_on += 1
                if above_on >= consecutive_required:
                    is_on = True
                    above_on = 0
                    below_off = 0
                    await bus.publish(Event.now(f"{tool}.on", src, v=v))
            else:
                above_on = 0
        else:
            if v <= off_threshold:
                below_off += 1
                if below_off >= consecutive_required:
                    is_on = False
                    above_on = 0
                    below_off = 0
                    await bus.publish(Event.now(f"{tool}.off", src, v=v))
            else:
                below_off = 0

        await asyncio.sleep(period)


async def run_adc_watch(cfg: AdcWatchConfig, bus: EventBus) -> None:
    """
    Quiet ADS1115 detector with hysteresis for:
    - Saw  (A0): publishes saw.on / saw.off as src=adc.a0
    - Lathe(A1): publishes lathe.on / lathe.off as src=adc.a1
    """
    import board  # type: ignore
    import busio  # type: ignore
    import adafruit_ads1x15.ads1115 as ADS  # type: ignore
    from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore

    if cfg.sample_hz <= 0:
        raise ValueError("sample_hz must be > 0")
    if cfg.consecutive_required < 1:
        raise ValueError("consecutive_required must be >= 1")
    if cfg.saw_channel != 0:
        raise ValueError("This watcher expects saw_channel=0 (A0)")
    if cfg.lathe_channel != 1:
        raise ValueError("This watcher expects lathe_channel=1 (A1)")

    period = 1.0 / cfg.sample_hz

    log.info(
        "ADC watch start: addr=0x%02x sample_hz=%.1f consec=%d | "
        "SAW A0 ON=%.3fV OFF=%.3fV | LATHE A1 ON=%.3fV OFF=%.3fV",
        cfg.i2c_address,
        cfg.sample_hz,
        cfg.consecutive_required,
        cfg.saw_on_threshold,
        cfg.saw_off_threshold,
        cfg.lathe_on_threshold,
        cfg.lathe_off_threshold,
    )

    i2c = busio.I2C(board.SCL, board.SDA)
    ads = ADS.ADS1115(i2c, address=cfg.i2c_address)

    saw = AnalogIn(ads, ADS.P0)
    lathe = AnalogIn(ads, ADS.P1)

    t_saw = asyncio.create_task(
        _watch_one(
            bus=bus,
            period=period,
            analog_in=saw,
            tool="saw",
            src="adc.a0",
            on_threshold=cfg.saw_on_threshold,
            off_threshold=cfg.saw_off_threshold,
            consecutive_required=cfg.consecutive_required,
        ),
        name="adc_watch_saw",
    )
    t_lathe = asyncio.create_task(
        _watch_one(
            bus=bus,
            period=period,
            analog_in=lathe,
            tool="lathe",
            src="adc.a1",
            on_threshold=cfg.lathe_on_threshold,
            off_threshold=cfg.lathe_off_threshold,
            consecutive_required=cfg.consecutive_required,
        ),
        name="adc_watch_lathe",
    )

    try:
        await asyncio.gather(t_saw, t_lathe)
    except asyncio.CancelledError:
        log.info("ADC watch cancelled")
        t_saw.cancel()
        t_lathe.cancel()
        await asyncio.gather(t_saw, t_lathe, return_exceptions=True)
        raise
