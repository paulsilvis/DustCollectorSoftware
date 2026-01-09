from __future__ import annotations

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
    AQM policy (simple, event-driven):
      - On aqm.bad: optionally fan ON; if severe: send FUN PAUSE to ESP32 (edge).
      - On aqm.good: optionally fan OFF.

    Notes:
      - AQM reader is expected to handle filtering and publish aqm.bad/aqm.good
        on transitions (not every sample).
      - safety.min_off_lockout_ms suppresses FAN ON for a short period after
        the fan was turned OFF (prevents rapid cycling).
    """
    fan_on_when_bad = bool(_cfg_get(cfg, ["aqm", "fan_on_when_bad"], False))
    pause_fun = bool(_cfg_get(cfg, ["safety", "pause_fun_on_severe_aqm"], False))
    min_off_lockout_ms = float(_cfg_get(cfg, ["safety", "min_off_lockout_ms"], 0.0))

    fan_pin = int(_cfg_get(cfg, ["gpio", "fan_ssr"], 24))
    fan_active_high = bool(_cfg_get(cfg, ["gpio", "fan_active_high"], True))
    fan = GPIOOut(fan_pin, active_high=fan_active_high)

    # Deterministic initial condition: force fan OFF at startup.
    try:
        fan.write(False)
    except Exception:
        log.exception("AQM policy: failed to initialize FAN OFF")

    q = bus.subscribe(maxsize=200)

    fan_is_on = False
    last_fan_off_at = time.monotonic()

    severe_latched = False

    log.info(
        "AQM policy running: fan_on_when_bad=%s pause_fun_on_severe=%s "
        "min_off_lockout_ms=%.0f fan_pin=%d fan_active_high=%s",
        fan_on_when_bad,
        pause_fun,
        min_off_lockout_ms,
        fan_pin,
        fan_active_high,
    )

    while True:
        ev = await q.get()
        if ev.type not in ("aqm.bad", "aqm.good"):
            continue

        is_bad = ev.type == "aqm.bad"
        severe = bool(ev.data.get("severe", False))

        # ---- Fan control ----
        if fan_on_when_bad:
            if is_bad:
                if not fan_is_on:
                    now = time.monotonic()

                    # After turning OFF, suppress turning ON for this lockout period.
                    if min_off_lockout_ms > 0:
                        elapsed_ms = (now - last_fan_off_at) * 1000.0
                        if elapsed_ms < min_off_lockout_ms:
                            log.info(
                                "AQM policy: FAN ON suppressed by lockout "
                                "(%.0fms < %.0fms)",
                                elapsed_ms,
                                min_off_lockout_ms,
                            )
                            continue

                    try:
                        fan.write(True)
                        fan_is_on = True
                        log.warning("AQM policy: FAN ON (bad air)")
                    except Exception:
                        log.exception("AQM policy: FAN ON failed")
            else:
                if fan_is_on:
                    try:
                        fan.write(False)
                        fan_is_on = False
                        last_fan_off_at = time.monotonic()
                        log.info("AQM policy: FAN OFF (good air)")
                    except Exception:
                        log.exception("AQM policy: FAN OFF failed")

        # ---- Severe -> pause fun (edge-triggered) ----
        if pause_fun and ser_tx is not None:
            if severe and not severe_latched:
                try:
                    ser_tx.write(b"FUN PAUSE\n")
                    log.error("AQM policy: SEVERE -> FUN PAUSE sent")
                except Exception:
                    log.exception("AQM policy: failed to write FUN PAUSE")
                severe_latched = True
            elif (not severe) and severe_latched:
                severe_latched = False
