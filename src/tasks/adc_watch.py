from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from ..event_bus import EventBus
from ..events import Event

log = logging.getLogger(__name__)


@dataclass(frozen=True)
class AdcWatchConfig:
    i2c_address: int = 0x48
    sample_hz: float = 10.0

    # Channels (single-ended): 0..3 => A0..A3
    saw_channel: int = 0
    lathe_channel: int = 1

    # Thresholds (VOLTS at ADC input)
    saw_on_threshold: float = 1.00
    saw_off_threshold: float = 0.30
    lathe_on_threshold: float = 0.040
    lathe_off_threshold: float = 0.025

    # Stability against noise
    consecutive_required: int = 3


def _pin_for_channel(ads1x15_mod, ch: int):
    pin_map = {
        0: ads1x15_mod.Pin.A0,
        1: ads1x15_mod.Pin.A1,
        2: ads1x15_mod.Pin.A2,
        3: ads1x15_mod.Pin.A3,
    }
    if ch not in pin_map:
        raise ValueError(f"channel must be 0..3 (got {ch})")
    return pin_map[ch]


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
    ADS1115 detector with hysteresis for:
      - Saw  (A0): publishes saw.on / saw.off as src=adc.a0
      - Lathe(A1): publishes lathe.on / lathe.off as src=adc.a1
    """

    # Hard dependency check: fail fast, fail loud
    try:
        import board  # type: ignore
        import busio  # type: ignore
        import adafruit_ads1x15.ads1115 as ADS  # type: ignore
        from adafruit_ads1x15 import ads1x15  # type: ignore
        from adafruit_ads1x15.analog_in import AnalogIn  # type: ignore
    except Exception as e:
        raise RuntimeError(
            "ADC watcher cannot start: ADS1115 stack not installed"
        ) from e

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

    saw_pin = _pin_for_channel(ads1x15, cfg.saw_channel)
    lathe_pin = _pin_for_channel(ads1x15, cfg.lathe_channel)

    saw = AnalogIn(ads, saw_pin)
    lathe = AnalogIn(ads, lathe_pin)

    try:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(
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
            tg.create_task(
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
    except asyncio.CancelledError:
        log.info("ADC watch cancelled")
        raise
