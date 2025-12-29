from __future__ import annotations

import asyncio
import logging

from ..event_bus import EventBus
from ..hardware.pcf_leds import PcfLedPair, PcfLedsConfig
from ..hardware.pcf_relays import PcfRelays, PcfRelaysConfig

log = logging.getLogger(__name__)

# Relays live on PCF8574 @ 0x21 (your proven wiring from yy_new.py)
LATHE_RELAY_OPEN_BIT = 5
LATHE_RELAY_CLOSE_BIT = 4

# Safety / behavior
RELAY_DEADTIME_S = 0.10
MAX_DRIVE_S = 6.0


async def run_lathe_gate_controller(bus: EventBus) -> None:
    """
    Lathe gate controller:
      - lathe.on  -> LED GREEN, drive OPEN for MAX_DRIVE_S then stop
      - lathe.off -> LED RED,   drive CLOSE for MAX_DRIVE_S then stop

    Concurrency:
      - One motion at a time. New command cancels prior motion safely.
    """
    q = bus.subscribe(maxsize=100)

    leds = PcfLedPair(
        PcfLedsConfig(
            bus=1,
            addr=0x20,
            green_bit=7,
            red_bit=3,
            active_low=True,
        )
    )

    relays = PcfRelays(
        PcfRelaysConfig(
            bus=1,
            addr=0x21,
            active_low=True,
        )
    )

    # Prevent interleaved open/close sequences and ensure "stop pair" is atomic
    motion_lock = asyncio.Lock()
    motion_task: asyncio.Task[None] | None = None

    async def _stop_relays() -> None:
        async with motion_lock:
            relays.stop_pair(LATHE_RELAY_OPEN_BIT, LATHE_RELAY_CLOSE_BIT)

    async def _start_open() -> None:
        async with motion_lock:
            # Ensure CLOSE is off first, then deadtime, then OPEN on
            relays.set_relay(LATHE_RELAY_CLOSE_BIT, False)
        await asyncio.sleep(RELAY_DEADTIME_S)
        async with motion_lock:
            relays.set_relay(LATHE_RELAY_OPEN_BIT, True)

    async def _start_close() -> None:
        async with motion_lock:
            # Ensure OPEN is off first, then deadtime, then CLOSE on
            relays.set_relay(LATHE_RELAY_OPEN_BIT, False)
        await asyncio.sleep(RELAY_DEADTIME_S)
        async with motion_lock:
            relays.set_relay(LATHE_RELAY_CLOSE_BIT, True)

    async def _drive_open_then_stop() -> None:
        try:
            await _start_open()
            await asyncio.sleep(MAX_DRIVE_S)
        finally:
            await _stop_relays()

    async def _drive_close_then_stop() -> None:
        try:
            await _start_close()
            await asyncio.sleep(MAX_DRIVE_S)
        finally:
            await _stop_relays()

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

    # Boot state
    leds.set_red()
    await _stop_relays()
    log.info("LATHE CTRL: boot -> CLOSED (Gate4 RED)")

    try:
        while True:
            ev = await q.get()

            if ev.type == "lathe.on":
                leds.set_green()
                log.info("LATHE CTRL: OPEN (Gate4 GREEN)")
                await _cancel_motion()
                motion_task = asyncio.create_task(_drive_open_then_stop())

            elif ev.type == "lathe.off":
                leds.set_red()
                log.info("LATHE CTRL: CLOSE (Gate4 RED)")
                await _cancel_motion()
                motion_task = asyncio.create_task(_drive_close_then_stop())

    except asyncio.CancelledError:
        log.info("Lathe gate controller cancelled")
        raise

    finally:
        try:
            await _cancel_motion()
        except Exception:
            log.exception("Lathe controller: motion cancel failed")

        try:
            await _stop_relays()
        except Exception:
            log.exception("Lathe controller: failed to stop relays")

        try:
            relays.close(restore=False)
        except Exception:
            log.exception("Lathe controller: failed to close relays")

        try:
            leds.close(restore=False)
        except Exception:
            log.exception("Lathe controller: failed to close LEDs")
