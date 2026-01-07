from __future__ import annotations

import argparse
import asyncio
import logging
from types import SimpleNamespace
from typing import Optional

from smbus2 import SMBus

from .config_loader import AppConfig
from .event_bus import EventBus
from .hardware.pcf_relays import PcfRelays, PcfRelaysConfig
from .hardware.uart import open_serial
from .util.logging_setup import setup_logging

log = logging.getLogger(__name__)

LED_PCF_ADDR = 0x20
RELAY_PCF_ADDR = 0x21


def _parse_args(argv: Optional[list[str]] = None) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="dustcollector")
    ap.add_argument("--config", required=True, help="Path to config YAML")
    return ap.parse_args(argv)


async def _event_logger(bus: EventBus) -> None:
    q = bus.subscribe(maxsize=100)
    try:
        while True:
            ev = await q.get()
            log.info("EVENT: %-10s src=%s data=%s", ev.type, ev.src, ev.data)
    except asyncio.CancelledError:
        log.info("Event logger cancelled")
        raise


def _leds_all_off_boot() -> None:
    try:
        bus = SMBus(1)
        try:
            before = int(bus.read_byte(LED_PCF_ADDR))
            bus.write_byte(LED_PCF_ADDR, 0x00)
            after = int(bus.read_byte(LED_PCF_ADDR))
        finally:
            bus.close()

        log.info(
            "LED init: PCF@0x20 before=0x%02x wrote=0x00 after=0x%02x",
            before,
            after,
        )
    except Exception:
        log.exception("LED init: failed to force all-off at boot")


async def _run_app(config_path: str) -> None:
    setup_logging()

    cfg = AppConfig.load(config_path)
    log.info("Boot: config=%s", config_path)

    _leds_all_off_boot()

    bus = EventBus()
    tasks: list[asyncio.Task[None]] = []

    # Relays on PCF8574 @ 0x21 (PCF->ULN2803 inverts -> relay inputs active-low)
    relays = PcfRelays(PcfRelaysConfig(bus=1, addr=RELAY_PCF_ADDR, active_low=False))
    relay_lock = asyncio.Lock()

    try:
        async with relay_lock:
            relays.all_off()
        log.info("Relay init: PCF@0x21 all OFF")
    except Exception:
        log.exception("Relay init: failed to force all-off at boot")
        raise

    # UART shared: RX=PMS1003, TX=ESP32 (ESP32 TX physically unconnected)
    uart_cfg = cfg.raw["uart"]
    aqm_port = str(uart_cfg["aqm_port"])
    baud = int(uart_cfg["baud"])
    aqm_ser = open_serial(aqm_port, baud)
    hw_uart = SimpleNamespace(ser=aqm_ser, serial=aqm_ser)
    log.info("AQM UART open: %s @ %d", aqm_port, baud)

    from .tasks.aqm_reader import aqm_reader
    from .tasks.aqm_policy import run_aqm_policy

    tasks.append(asyncio.create_task(aqm_reader(bus, cfg, hw_uart), name="aqm_reader"))
    log.info("AQM reader started")

    tasks.append(asyncio.create_task(run_aqm_policy(bus, cfg, ser_tx=aqm_ser), name="aqm_policy"))
    log.info("AQM policy started")

    tasks.append(asyncio.create_task(_event_logger(bus), name="event_logger"))

    # Gate controllers
    from .tasks.lathe_gate_controller import run_lathe_gate_controller
    from .tasks.saw_gate_controller import run_saw_gate_controller

    tasks.append(
        asyncio.create_task(
            run_lathe_gate_controller(bus, relays, relay_lock),
            name="lathe_gate_ctrl",
        )
    )
    tasks.append(
        asyncio.create_task(
            run_saw_gate_controller(bus, relays, relay_lock),
            name="saw_gate_ctrl",
        )
    )
    log.info("Gate controllers started")

    # ADC watch
    from .tasks.adc_watch import AdcWatchConfig, run_adc_watch

    adc_cfg = AdcWatchConfig(
        i2c_address=0x48,
        sample_hz=10.0,
        lathe_channel=1,
        lathe_on_threshold=0.040,
        lathe_off_threshold=0.025,
        consecutive_required=3,
    )
    tasks.append(asyncio.create_task(run_adc_watch(adc_cfg, bus), name="adc_watch"))
    log.info("ADC watch started")

    # Collector SSR controller
    from .tasks.collector_ssr_controller import run_collector_ssr_controller

    tasks.append(
        asyncio.create_task(
            run_collector_ssr_controller(bus, cfg),
            name="collector_ssr",
        )
    )
    log.info("Collector SSR controller started")

    try:
        while True:
            await asyncio.sleep(3600.0)
    finally:
        log.info("Shutdown: cancelling tasks")
        for t in tasks:
            t.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

        try:
            async with relay_lock:
                relays.all_off()
        except Exception:
            log.exception("Shutdown: failed to force all relays off")

        try:
            relays.close(restore=False)
        except Exception:
            log.exception("Shutdown: failed to close relay bus")

        try:
            aqm_ser.close()
        except Exception:
            log.exception("Shutdown: failed to close AQM serial")

        log.info("Shutdown complete")


def main(argv: Optional[list[str]] = None) -> int:
    args = _parse_args(argv)
    try:
        asyncio.run(_run_app(args.config))
        return 0
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt: exiting")
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
