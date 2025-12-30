from __future__ import annotations

from ..domain.gate import Gate
from ..domain.leds import Leds
from ..system.event_bus import EventBus
from .gate_task_common import GateTaskConfig, run_gate_task


async def run_lathe_gate_controller(
    bus: EventBus,
    gate: Gate,
    leds: Leds,
) -> None:
    cfg = GateTaskConfig(
        device_name="lathe",
        on_led=Leds.LATHE_ON,
        off_led=Leds.LATHE_OFF,
    )
    await run_gate_task(bus, gate, leds, cfg)
