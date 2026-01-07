from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from ..event_bus import EventBus
from ..hardware.gpio import GPIOOut

log = logging.getLogger("aqm_policy")


def _cfg_get(cfg: Any, keys: list[str], default: Any) -> Any:
    raw = getattr(cfg, "raw", None)
    if not isinstance(raw, dict):
        return default
    cur: Any = raw
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    return cur


async def run_aqm_policy(bus: EventBus, cfg: Any, *, ser_tx: Optional[Any]) -> None:
    """
    AQM policy:
    - On aqm.bad: optionally fan ON; if severe: send FUN PAUSE to ESP32.
    - On aqm.good: optionally fan OFF.
    """
    fan_on_when_bad = bool(_cfg_get(cfg, ["aqm", "fan_on_when_bad"], False))
    pause_fun = bool(_cfg_get(cfg, ["safety", "pause_fun_on_severe_aqm"], False))
    min_off_lockout_ms = int(_cfg_get(cfg, ["safety", "min_off_lockout_ms"], 0))

    fan_pin = int(_cfg_get(cfg, ["gpio", "fan_ssr"], 24))
    fan = GPIOOut(fan_pin, active_high=True)

    q = bus.subscribe(maxsize=200)

    fan_is_on = False
    last_fan_off_at = 0.0

    log.info(
        "AQM policy running: fan_on_when_bad=%s pause_fun_on_severe=%s "
        "min_off_lockout_ms=%d fan_pin=%d",
        fan_on_when_bad,
        pause_fun,
        min_off_lockout_ms,
        fan_pin,
    )

    while True:
        ev = await q.get()
        if ev.type not in ("aqm.bad", "aqm.good"):
            continue

        severe = bool(ev.data.get("severe", False))

        # ---- Fan control ----
        if fan_on_when_bad:
            if ev.type == "aqm.bad":
                if not fan_is_on:
                    fan.write(True)
                    fan_is_on = True
                    log.warning("AQM policy: FAN ON (bad air)")
            else:  # aqm.good
                if fan_is_on:
                    now = time.monotonic()
                    if min_off_lockout_ms > 0:
                        elapsed_ms = (now - last_fan_off_at) * 1000.0
                        if elapsed_ms < min_off_lockout_ms:
                            continue
                    fan.write(False)
                    fan_is_on = False
                    last_fan_off_at = now
                    log.info("AQM policy: FAN OFF (good air)")

        # ---- Severe -> pause fun ----
        if pause_fun and severe and ser_tx is not None:
            try:
                ser_tx.write(b"FUN PAUSE\n")
                log.error("AQM policy: SEVERE -> FUN PAUSE sent")
            except Exception:
                log.exception("AQM policy: failed to write FUN PAUSE")
