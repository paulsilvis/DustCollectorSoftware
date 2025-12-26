from __future__ import annotations

import argparse
import asyncio
import logging
import os

from .config_loader import AppConfig
from .event_bus import EventBus
from .hardware.hw import get_hardware
from .tasks.adc_watch import adc_watch
from .tasks.collector_controller import collector_controller
from .tasks.display_status import display_status
from .tasks.funhouse import funhouse
from .tasks.gate_controller import gate_controller
from .tasks.machine_manager import machine_manager
from .tasks.sys_monitor import sys_monitor
from .util.logging_setup import setup_logging

# NOTE: This name is a little misleading in your tree: it's under hardware/,
# but used like a task. Leaving as-is; we can rename later when it's boring.
from .hardware.pms1003 import aqm_reader


async def run(config_path: str) -> None:
    cfg = AppConfig.load(config_path)
    setup_logging(cfg.log_level)
    log = logging.getLogger("main")

    hw = get_hardware(cfg)
    bus = EventBus()

    log.info("Starting DustCollector")

    tasks = [
        asyncio.create_task(adc_watch(bus, cfg, hw)),
        asyncio.create_task(machine_manager(bus)),
        asyncio.create_task(gate_controller(bus, cfg, hw)),
        asyncio.create_task(collector_controller(bus, cfg, hw)),
        asyncio.create_task(aqm_reader(bus, cfg, hw)),
        asyncio.create_task(display_status(bus, cfg, hw)),
        asyncio.create_task(sys_monitor(bus, cfg, hw)),
        asyncio.create_task(funhouse(bus, cfg, hw)),
    ]

    try:
        await asyncio.gather(*tasks)
    except asyncio.CancelledError:
        pass


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--config",
        default=os.environ.get("CONFIG_PATH", "config/config.yaml"),
    )
    args = ap.parse_args()
    asyncio.run(run(args.config))


if __name__ == "__main__":
    main()
