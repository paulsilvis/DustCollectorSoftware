from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Optional

from ..events import Event
from ..event_bus import EventBus

log = logging.getLogger("aqm_reader")

START1 = 0x42
START2 = 0x4D
FRAME_LEN = 32


# Adafruit SSD1306 OLED support (SSD1306 128x64 over I2C @ 0x3C).
OLED_OK = True
try:
    import board  # type: ignore
    import busio  # type: ignore
    from adafruit_ssd1306 import SSD1306_I2C  # type: ignore
    from PIL import Image, ImageDraw, ImageFont  # type: ignore
except Exception:
    OLED_OK = False


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


def _get_serial(hw: Any) -> Any:
    ser = getattr(hw, "ser", None)
    if ser is None:
        ser = getattr(hw, "serial", None)
    if ser is None:
        raise RuntimeError("aqm_reader: hw has no 'ser' or 'serial' attribute")
    return ser


def _checksum_ok(frame: bytes) -> bool:
    """
    Frame checksum: sum of first 30 bytes (0..29) equals last 2 bytes (30..31).
    """
    if len(frame) != FRAME_LEN:
        return False
    expected = (frame[30] << 8) | frame[31]
    actual = sum(frame[:30]) & 0xFFFF
    return actual == expected


def _find_frame_blocking(ser: Any) -> Optional[bytes]:
    """
    Blocking scan for 0x42 0x4D, then read the remaining 30 bytes.

    Returns:
      - a valid 32-byte frame
      - None on timeout / EOF-ish behavior
    """
    while True:
        b1 = ser.read(1)
        if not b1:
            return None
        if b1[0] != START1:
            continue

        b2 = ser.read(1)
        if not b2:
            return None
        if b2[0] != START2:
            continue

        rest = ser.read(30)
        if len(rest) != 30:
            return None

        frame = b1 + b2 + rest
        if _checksum_ok(frame):
            return frame

        # Checksum failed; resync by continuing scan
        # (same behavior as your demo script, but without printing every time).
        continue


def _parse_metrics(frame: bytes, use_cf1: bool) -> dict[str, int]:
    """
    Plantower PMS frame fields:
      CF=1:
        PM1.0  bytes 4-5
        PM2.5  bytes 6-7
        PM10   bytes 8-9
      Atmospheric:
        PM1.0  bytes 10-11
        PM2.5  bytes 12-13
        PM10   bytes 14-15
    """
    if use_cf1:
        pm1_0 = (frame[4] << 8) | frame[5]
        pm2_5 = (frame[6] << 8) | frame[7]
        pm10 = (frame[8] << 8) | frame[9]
    else:
        pm1_0 = (frame[10] << 8) | frame[11]
        pm2_5 = (frame[12] << 8) | frame[13]
        pm10 = (frame[14] << 8) | frame[15]
    return {"pm1_0": int(pm1_0), "pm2_5": int(pm2_5), "pm10": int(pm10)}


def _clamp_bad_off_threshold(bad_off_th: int, bad_on_th: int) -> int:
    if bad_off_th >= bad_on_th:
        return bad_on_th - 1
    return bad_off_th


class _Oled:
    """
    SSD1306 128x64 at I2C 0x3C using Adafruit SSD1306_I2C + PIL.

    4 lines:
      1) STATUS: GOOD/BAD/SEVERE
      2) PM1.0: <val>
      3) PM2.5: <val>
      4) PM10 : <val>
    """

    def __init__(self) -> None:
        self.enabled = False
        self._disp = None
        self._w = 0
        self._h = 0
        self._image = None
        self._draw = None
        self._font = None
        self._last_payload: Optional[str] = None

        if not OLED_OK:
            log.warning("OLED: libs not available in this python; OLED disabled.")
            return

        try:
            i2c = busio.I2C(board.SCL, board.SDA)
            self._disp = SSD1306_I2C(128, 64, i2c, addr=0x3C)
            self._w = int(getattr(self._disp, "width", 128))
            self._h = int(getattr(self._disp, "height", 64))
            self._image = Image.new("1", (self._w, self._h))
            self._draw = ImageDraw.Draw(self._image)
            self._font = ImageFont.load_default()
            self.enabled = True
            self.show_waiting()
            log.info("OLED: init OK (SSD1306 128x64 @ 0x3C).")
        except Exception as e:
            log.warning("OLED: init FAILED; disabled: %s", e)

    def _clear(self) -> None:
        assert self._draw is not None
        self._draw.rectangle((0, 0, self._w, self._h), outline=0, fill=0)

    def _flush(self) -> None:
        assert self._disp is not None
        assert self._image is not None
        self._disp.image(self._image)
        self._disp.show()

    def show_waiting(self) -> None:
        if not self.enabled:
            return
        assert self._draw is not None
        assert self._font is not None

        payload = "WAITING"
        if payload == self._last_payload:
            return
        self._last_payload = payload

        self._clear()
        self._draw.text((0, 0), "AQM: WAITING", font=self._font, fill=255)
        self._draw.text((0, 16), "for PMS1003", font=self._font, fill=255)
        self._draw.text((0, 32), "frames...", font=self._font, fill=255)
        self._flush()

    def show(self, status: str, pm1_0: int, pm2_5: int, pm10: int) -> None:
        if not self.enabled:
            return
        assert self._draw is not None
        assert self._font is not None

        payload = f"{status}|{pm1_0}|{pm2_5}|{pm10}"
        if payload == self._last_payload:
            return
        self._last_payload = payload

        self._clear()
        self._draw.text((0, 0), status, font=self._font, fill=255)
        self._draw.text((0, 16), f"PM1.0: {pm1_0}", font=self._font, fill=255)
        self._draw.text((0, 32), f"PM2.5: {pm2_5}", font=self._font, fill=255)
        self._draw.text((0, 48), f"PM10 : {pm10}", font=self._font, fill=255)
        self._flush()


async def aqm_reader(bus: EventBus, cfg: Any, hw: Any) -> None:
    """
    RX-only PMS reader using the proven blocking header-scan algorithm,
    executed in a thread (asyncio.to_thread) so we don't block the event loop.

    Publishes:
      - aqm.metrics {pm1_0, pm2_5, pm10}
      - aqm.good / aqm.bad {pm2_5, severe}

    OLED:
      - updates every valid frame (status + three readings)
    """
    ser = _get_serial(hw)

    # Make the serial reads behave like the demo:
    # blocking with a timeout so the scanner can keep syncing.
    try:
        ser.timeout = float(_cfg_get(cfg, ["aqm", "serial_timeout_s"], 2.0))
    except Exception:
        pass

    if hasattr(ser, "reset_input_buffer"):
        try:
            ser.reset_input_buffer()
        except Exception:
            pass

    interval_s = float(_cfg_get(cfg, ["aqm", "interval_s"], 0.8))

    bad_on_th = int(_cfg_get(cfg, ["aqm", "bad_threshold"], 35))
    sev_th = int(_cfg_get(cfg, ["aqm", "severe_threshold"], 75))

    bad_hyst = int(_cfg_get(cfg, ["aqm", "bad_hysteresis"], 5))
    bad_off_th = int(
        _cfg_get(cfg, ["aqm", "bad_off_threshold"], bad_on_th - bad_hyst)
    )
    bad_off_th = _clamp_bad_off_threshold(bad_off_th, bad_on_th)

    # Match your demo script by default: CF=1 values (bytes 4..9).
    use_cf1 = bool(_cfg_get(cfg, ["aqm", "use_cf1"], True))

    is_bad = False
    oled = _Oled()

    last_pm25: Optional[int] = None
    last_pub_t = time.monotonic()

    log.info(
        "AQM reader running (interval_s=%.3f bad_on=%d bad_off=%d severe=%d use_cf1=%s) [RX-only]",
        interval_s,
        bad_on_th,
        bad_off_th,
        sev_th,
        use_cf1,
    )

    while True:
        # Get the next valid frame using the robust scanner in a thread.
        frame = await asyncio.to_thread(_find_frame_blocking, ser)
        if frame is None:
            # Timeout: nothing read; keep OLED in WAITING and loop.
            oled.show_waiting()
            await asyncio.sleep(0.1)
            continue

        metrics = _parse_metrics(frame, use_cf1=use_cf1)
        pm1_0 = int(metrics["pm1_0"])
        pm25 = int(metrics["pm2_5"])
        pm10 = int(metrics["pm10"])

        now_t = time.monotonic()
        dt = now_t - last_pub_t
        last_pub_t = now_t
        changed = (last_pm25 is None) or (pm25 != last_pm25)
        last_pm25 = pm25
        log.warning(
            "AQM: sample dt=%.2fs pm2_5=%d %s pm1_0=%d pm10=%d",
            dt,
            pm25,
            "CHANGED" if changed else "same",
            pm1_0,
            pm10,
        )

        await bus.publish(Event.now("aqm.metrics", "aqm.pms1003", **metrics))

        # Hysteresis:
        if is_bad:
            if pm25 <= bad_off_th:
                is_bad = False
        else:
            if pm25 >= bad_on_th:
                is_bad = True

        severe = pm25 >= sev_th
        await bus.publish(
            Event.now(
                "aqm.bad" if is_bad else "aqm.good",
                "aqm.pms1003",
                pm2_5=pm25,
                severe=severe,
            )
        )

        status = "SEVERE" if severe else ("BAD" if is_bad else "GOOD")
        oled.show(status=status, pm1_0=pm1_0, pm2_5=pm25, pm10=pm10)

        # Keep your existing cadence (even though frames pace us already).
        await asyncio.sleep(interval_s)
