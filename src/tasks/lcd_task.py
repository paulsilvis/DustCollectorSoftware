from __future__ import annotations

import asyncio
import logging
from datetime import datetime

from RPLCD.i2c import CharLCD

from ..event_bus import EventBus

log = logging.getLogger(__name__)

LCD_ADDRESS = 0x3F
LCD_COLS = 20
LCD_ROWS = 4
IDLE_ROTATE_S = 5        # seconds between idle page flips
CLOCK_UPDATE_S = 1.0     # event-wait timeout; drives the 1-second clock tick


def _init_lcd() -> CharLCD:
    return CharLCD(
        i2c_expander="PCF8574",
        address=LCD_ADDRESS,
        port=1,
        cols=LCD_COLS,
        rows=LCD_ROWS,
        dotsize=8,
    )


class _Display:
    """Thin wrapper around CharLCD with row-safe writes."""

    def __init__(self, lcd: CharLCD) -> None:
        self._lcd = lcd

    def row(self, r: int, text: str) -> None:
        self._lcd.cursor_pos = (r, 0)
        self._lcd.write_string(text.ljust(LCD_COLS)[:LCD_COLS])

    def clear(self) -> None:
        self._lcd.clear()

    # ------------------------------------------------------------------ pages

    def show_tool(self, tool: str, other_tool: str | None = None) -> None:
        """Full-screen alert when a tool is active."""
        self.clear()
        self.row(0, f"  {tool.upper()} ON")
        self.row(1, "  Gate:      OPEN")
        self.row(2, "  Collector: RUNNING")
        if other_tool:
            self.row(3, f"  {other_tool.upper()} also ON")
        else:
            self.row(3, "")

    def show_both_tools(self) -> None:
        self.clear()
        self.row(0, "  SAW + LATHE ON")
        self.row(1, "  Gates:     OPEN")
        self.row(2, "  Collector: RUNNING")
        self.row(3, "")

    def show_clock(self) -> None:
        now = datetime.now()
        self.clear()
        self.row(0, "  Dust Collector")
        self.row(1, "  All tools off")
        self.row(2, f"  {now.strftime('%a %b %d %Y')}")
        self.row(3, f"  {now.strftime('%H:%M:%S')}")

    def show_status(self) -> None:
        now = datetime.now()
        self.clear()
        self.row(0, "  System idle")
        self.row(1, f"  {now.strftime('%H:%M:%S')}")
        self.row(2, "  Shop: all clear")
        self.row(3, "")

    def show_goodbye(self) -> None:
        self.clear()
        self.row(1, "  Dust Collector")
        self.row(2, "  Shutting down...")


# Ordered list of idle pages to rotate through
_IDLE_PAGES = ["clock", "status"]


async def run_lcd_task(bus: EventBus) -> None:
    """
    LCD display task.

    Idle: rotates between clock and status pages every IDLE_ROTATE_S seconds.
    Active: interrupts with a full-screen tool-on alert.
    Subscribes to: saw.on / saw.off / lathe.on / lathe.off
    """
    try:
        lcd = _init_lcd()
        display = _Display(lcd)
        log.info("LCD task: display initialised at 0x%02x", LCD_ADDRESS)
    except Exception:
        log.exception("LCD task: init failed — display task will not run")
        return

    q = bus.subscribe(maxsize=50)

    saw_on = False
    lathe_on = False
    idle_page_idx = 0
    idle_ticks = 0          # counts 1-second ticks while idle

    def _refresh_active() -> None:
        if saw_on and lathe_on:
            display.show_both_tools()
        elif saw_on:
            display.show_tool("Saw")
        elif lathe_on:
            display.show_tool("Lathe")

    def _refresh_idle() -> None:
        page = _IDLE_PAGES[idle_page_idx % len(_IDLE_PAGES)]
        if page == "clock":
            display.show_clock()
        elif page == "status":
            display.show_status()

    # Draw initial idle screen
    _refresh_idle()

    try:
        while True:
            try:
                event = await asyncio.wait_for(q.get(), timeout=CLOCK_UPDATE_S)

                if event.type == "saw.on":
                    saw_on = True
                    _refresh_active()

                elif event.type == "saw.off":
                    saw_on = False
                    if lathe_on:
                        _refresh_active()
                    else:
                        idle_ticks = 0
                        _refresh_idle()

                elif event.type == "lathe.on":
                    lathe_on = True
                    _refresh_active()

                elif event.type == "lathe.off":
                    lathe_on = False
                    if saw_on:
                        _refresh_active()
                    else:
                        idle_ticks = 0
                        _refresh_idle()

                # Ignore all other event types silently

            except asyncio.TimeoutError:
                # One-second tick
                if saw_on or lathe_on:
                    pass  # active display doesn't need a clock
                else:
                    idle_ticks += 1
                    if idle_ticks >= IDLE_ROTATE_S:
                        idle_ticks = 0
                        idle_page_idx += 1
                    _refresh_idle()

    except asyncio.CancelledError:
        log.info("LCD task: cancelled")
        display.show_goodbye()
        raise
