from __future__ import annotations

import asyncio
import logging

from ..event_bus import EventBus
from ..hardware.pcf_leds import PcfLedPair, PcfLedsConfig
from ..hardware.pcf_relays import PcfRelays

log = logging.getLogger(__name__)

# LED bits on PCF @ 0x20
LATHE_LED_GREEN_BIT = 7
LATHE_LED_RED_BIT = 3

# Relay bits on PCF @ 0x21
# Canonical convention (empirically verified):
#   odd bit  = CLOSE
#   even bit = OPEN
LATHE_RELAY_CLOSE_BIT = 5
LATHE_RELAY_OPEN_BIT = 4

RELAY_DEADTIME_S = 0.10
MAX_DRIVE_S = 6.0


async def run_lathe_gate_controller(
    bus: EventBus,
    relays: PcfRelays,
    relay_lock: asyncio.Lock,
) -> None:
    """
    Lathe gate controller.

    Events:
      lathe.on  -> LED GREEN, drive OPEN for MAX_DRIVE_S, then stop
      lathe.off -> LED RED,   drive CLOSE for MAX_DRIVE_S, then stop

    relay_lock MUST be shared across all controllers touching relays@0x21.
    """
    q = bus.subscribe(maxsize=100)

    leds = PcfLedPair(
        PcfLedsConfig(
            bus=1,
            addr=0x20,
            green_bit=LATHE_LED_GREEN_BIT,
            red_bit=LATHE_LED_RED_BIT,
            active_low=False,  # <-- ACTIVE-HIGH LED board
        )
    )

    motion_task: asyncio.Task[None] | None = None

    async def _relay_stop() -> None:
        async with relay_lock:
            relays.stop_pair(LATHE_RELAY_OPEN_BIT, LATHE_RELAY_CLOSE_BIT)

    async def _relay_start_open() -> None:
        async with relay_lock:
            relays.set_relay(LATHE_RELAY_CLOSE_BIT, False)
        await asyncio.sleep(RELAY_DEADTIME_S)
        async with relay_lock:
            relays.set_relay(LATHE_RELAY_OPEN_BIT, True)

    async def _relay_start_close() -> None:
        async with relay_lock:
            relays.set_relay(LATHE_RELAY_OPEN_BIT, False)
        await asyncio.sleep(RELAY_DEADTIME_S)
        async with relay_lock:
            relays.set_relay(LATHE_RELAY_CLOSE_BIT, True)

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

    # Boot state
    leds.set_red()
    await _relay_stop()
    log.info("LATHE CTRL: boot -> CLOSED (Gate RED)")

    try:
        while True:
            ev = await q.get()

            if ev.type == "lathe.on":
                leds.set_green()
                log.info("LATHE CTRL: OPEN (Gate GREEN)")
                await _cancel_motion()
                motion_task = asyncio.create_task(_drive_open_then_stop())

            elif ev.type == "lathe.off":
                leds.set_red()
                log.info("LATHE CTRL: CLOSE (Gate RED)")
                await _cancel_motion()
                motion_task = asyncio.create_task(_drive_close_then_stop())

    except asyncio.CancelledError:
        log.info("Lathe gate controller cancelled")
        raise
    finally:
        try:
            await _cancel_motion()
            await _relay_stop()
        except Exception:
            log.exception("Lathe controller: shutdown relay stop failed")
        try:
            leds.close(restore=False)
        except Exception:
            log.exception("Lathe controller: failed to close LEDs")
