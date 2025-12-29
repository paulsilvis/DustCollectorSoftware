from __future__ import annotations

import asyncio
import logging

from ..event_bus import EventBus
from ..hardware.pcf_leds import PcfLedPair, PcfLedsConfig
from ..hardware.pcf_relays import PcfRelays

log = logging.getLogger(__name__)

SAW_LED_GREEN_BIT = 6
SAW_LED_RED_BIT = 2

# Empirically verified:
# - relay bit 6 energize -> gate OPENS
# - relay bit 7 energize -> gate CLOSES
SAW_RELAY_OPEN_BIT = 6
SAW_RELAY_CLOSE_BIT = 7

RELAY_DEADTIME_S = 0.10
MAX_DRIVE_S = 6.0


async def run_saw_gate_controller(
    bus: EventBus,
    relays: PcfRelays,
    relay_lock: asyncio.Lock,
) -> None:
    """
    Saw gate controller:
    - saw.on  -> LED GREEN, drive OPEN for MAX_DRIVE_S then stop
    - saw.off -> LED RED,   drive CLOSE for MAX_DRIVE_S then stop
    """
    q = bus.subscribe(maxsize=100)

    leds = PcfLedPair(
        PcfLedsConfig(
            bus=1,
            addr=0x20,
            green_bit=SAW_LED_GREEN_BIT,
            red_bit=SAW_LED_RED_BIT,
            active_low=True,
        )
    )

    motion_task: asyncio.Task[None] | None = None

    async def _relay_stop() -> None:
        async with relay_lock:
            relays.stop_pair(SAW_RELAY_OPEN_BIT, SAW_RELAY_CLOSE_BIT)

    async def _relay_start_open() -> None:
        async with relay_lock:
            relays.set_relay(SAW_RELAY_CLOSE_BIT, False)
        await asyncio.sleep(RELAY_DEADTIME_S)
        async with relay_lock:
            relays.set_relay(SAW_RELAY_OPEN_BIT, True)

    async def _relay_start_close() -> None:
        async with relay_lock:
            relays.set_relay(SAW_RELAY_OPEN_BIT, False)
        await asyncio.sleep(RELAY_DEADTIME_S)
        async with relay_lock:
            relays.set_relay(SAW_RELAY_CLOSE_BIT, True)

    async def _drive_open_then_stop() -> None:
        try:
            await _relay_start_open()
            await asyncio.sleep(MAX_DRIVE_S)
        finally:
            await _relay_stop()

    async def _drive_close_then_stop() -> None:
        try:
            await _relay_start_close()
            await asyncio.sleep(MAX_DRIVE_S)
        finally:
            await _relay_stop()

    async def _cancel_motion() -> None:
        nonlocal motion_task
        if motion_task is None:
            return
        motion_task.cancel()
        try:
            await motion_task
        except asyncio.CancelledError:
            pass
        finally:
            motion_task = None

    leds.set_red()
    await _relay_stop()
    log.info("SAW CTRL: boot -> CLOSED (Saw RED)")

    try:
        while True:
            ev = await q.get()

            if ev.type == "saw.on":
                leds.set_green()
                log.info("SAW CTRL: OPEN (Saw GREEN)")
                await _cancel_motion()
                motion_task = asyncio.create_task(_drive_open_then_stop())

            elif ev.type == "saw.off":
                leds.set_red()
                log.info("SAW CTRL: CLOSE (Saw RED)")
                await _cancel_motion()
                motion_task = asyncio.create_task(_drive_close_then_stop())

    except asyncio.CancelledError:
        log.info("Saw gate controller cancelled")
        raise
    finally:
        try:
            await _cancel_motion()
            await _relay_stop()
        except Exception:
            log.exception("Saw controller: shutdown relay stop failed")
        try:
            leds.close(restore=False)
        except Exception:
            log.exception("Saw controller: failed to close LEDs")
