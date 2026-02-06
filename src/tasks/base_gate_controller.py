from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass

from ..event_bus import EventBus
from ..hardware.pcf_leds import PcfLedPair, PcfLedsConfig
from ..hardware.pcf_relays import PcfRelays

log = logging.getLogger(__name__)

RELAY_DEADTIME_S = 0.10
MAX_DRIVE_S = 6.0


@dataclass
class GateConfig:
    """Configuration for a gate controller."""
    name: str
    event_on: str
    event_off: str
    led_green_bit: int
    led_red_bit: int
    relay_open_bit: int
    relay_close_bit: int


class BaseGateController:
    """
    Base gate controller with common logic for relay-driven gates.
    
    Handles:
    - LED state (green=open, red=closed)
    - Relay control with deadtime protection
    - Timed gate motion with auto-stop
    - Safe cancellation and cleanup
    """

    def __init__(
        self,
        bus: EventBus,
        relays: PcfRelays,
        relay_lock: asyncio.Lock,
        config: GateConfig,
    ):
        self.bus = bus
        self.relays = relays
        self.relay_lock = relay_lock
        self.config = config
        
        self.leds = PcfLedPair(
            PcfLedsConfig(
                bus=1,
                addr=0x20,
                green_bit=config.led_green_bit,
                red_bit=config.led_red_bit,
                active_low=False,  # ACTIVE-HIGH LED board
            )
        )
        
        self.motion_task: asyncio.Task[None] | None = None

    async def _relay_stop(self) -> None:
        """Stop both relays."""
        async with self.relay_lock:
            self.relays.stop_pair(
                self.config.relay_open_bit,
                self.config.relay_close_bit
            )

    async def _relay_start_open(self) -> None:
        """Start opening the gate (with deadtime protection)."""
        async with self.relay_lock:
            self.relays.set_relay(self.config.relay_close_bit, False)
        await asyncio.sleep(RELAY_DEADTIME_S)
        async with self.relay_lock:
            self.relays.set_relay(self.config.relay_open_bit, True)

    async def _relay_start_close(self) -> None:
        """Start closing the gate (with deadtime protection)."""
        async with self.relay_lock:
            self.relays.set_relay(self.config.relay_open_bit, False)
        await asyncio.sleep(RELAY_DEADTIME_S)
        async with self.relay_lock:
            self.relays.set_relay(self.config.relay_close_bit, True)

    async def _drive_open_then_stop(self) -> None:
        """Drive gate open for MAX_DRIVE_S, then stop."""
        try:
            await self._relay_start_open()
            await asyncio.sleep(MAX_DRIVE_S)
        finally:
            await self._relay_stop()

    async def _drive_close_then_stop(self) -> None:
        """Drive gate closed for MAX_DRIVE_S, then stop."""
        try:
            await self._relay_start_close()
            await asyncio.sleep(MAX_DRIVE_S)
        finally:
            await self._relay_stop()

    async def _cancel_motion(self) -> None:
        """Cancel any in-progress motion task."""
        if self.motion_task is None:
            return
        self.motion_task.cancel()
        try:
            await self.motion_task
        except asyncio.CancelledError:
            pass
        finally:
            self.motion_task = None

    async def run(self) -> None:
        """
        Main controller loop.
        
        Subscribes to events and controls gate motion based on:
        - {name}.on  -> LED GREEN, drive OPEN for MAX_DRIVE_S then stop
        - {name}.off -> LED RED,   drive CLOSE for MAX_DRIVE_S then stop
        """
        q = self.bus.subscribe(maxsize=100)

        # Boot state: closed
        self.leds.set_red()
        await self._relay_stop()
        log.info(f"{self.config.name.upper()} CTRL: boot -> CLOSED (RED)")

        try:
            while True:
                ev = await q.get()

                if ev.type == self.config.event_on:
                    self.leds.set_green()
                    log.info(f"{self.config.name.upper()} CTRL: OPEN (GREEN)")
                    await self._cancel_motion()
                    self.motion_task = asyncio.create_task(
                        self._drive_open_then_stop()
                    )

                elif ev.type == self.config.event_off:
                    self.leds.set_red()
                    log.info(f"{self.config.name.upper()} CTRL: CLOSE (RED)")
                    await self._cancel_motion()
                    self.motion_task = asyncio.create_task(
                        self._drive_close_then_stop()
                    )

        except asyncio.CancelledError:
            log.info(f"{self.config.name} gate controller cancelled")
            raise
        finally:
            await self._cleanup()

    async def _cleanup(self) -> None:
        """Cleanup resources on shutdown."""
        try:
            await self._cancel_motion()
            await self._relay_stop()
        except Exception:
            log.exception(f"{self.config.name} controller: shutdown relay stop failed")
        
        try:
            self.leds.close(restore=False)
        except Exception:
            log.exception(f"{self.config.name} controller: failed to close LEDs")
