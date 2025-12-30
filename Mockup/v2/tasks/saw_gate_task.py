from __future__ import annotations

from ..domain.gate import Gate
from ..domain.leds import Leds
from ..system.event_bus import EventBus
from .gate_task_common import GateTaskConfig, run_gate_task


async def run_saw_gate_controller(
    bus: EventBus,
    gate: Gate,
    leds: Leds,
) -> None:
    cfg = GateTaskConfig(
        device_name="saw",
        on_led=Leds.SAW_ON,
        off_led=Leds.SAW_OFF,
    )
    await run_gate_task(bus, gate, leds, cfg)
