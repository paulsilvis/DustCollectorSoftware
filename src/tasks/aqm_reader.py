from __future__ import annotations

import asyncio
import logging
import time
from collections import deque
from typing import Any, Deque, Optional

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

        # Checksum failed; resync by continuing scan.
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


def _avg_last(hist: Deque[int], n: int) -> int:
    if n <= 1 or len(hist) <= 1:
        return int(hist[-1])
    k = min(n, len(hist))
    tail = list(hist)[-k:]
    return int(round(sum(tail) / k))


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
      - aqm.metrics {pm1_0, pm2_5, pm10, ...}
      - aqm.good / aqm.bad {pm2_5, severe}

    OLED:
      - updates every valid frame (status + three readings)

    Adaptive filtering:
      - filter_window_good is used when air is GOOD
      - filter_window_bad is used when air is BAD (typically larger, to suppress
        fan-induced turbulence fluctuations)
    """
    ser = _get_serial(hw)

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
    show_values = bool(_cfg_get(cfg, ["aqm", "show_values"], False))

    win_good = int(_cfg_get(cfg, ["aqm", "filter_window_good"], 5))
    if win_good < 1:
        win_good = 1

    bad_mult = float(_cfg_get(cfg, ["aqm", "filter_window_bad_mult"], 5.0))
    if bad_mult < 1.0:
        bad_mult = 1.0

    win_bad_cfg = int(_cfg_get(cfg, ["aqm", "filter_window_bad"], 0))
    if win_bad_cfg >= 1:
        win_bad = win_bad_cfg
    else:
        win_bad = int(round(win_good * bad_mult))
        if win_bad < 1:
            win_bad = 1

    max_win = max(win_good, win_bad)

    pm1_hist: Deque[int] = deque(maxlen=max_win)
    pm25_hist: Deque[int] = deque(maxlen=max_win)
    pm10_hist: Deque[int] = deque(maxlen=max_win)

    bad_on_th = int(_cfg_get(cfg, ["aqm", "bad_threshold"], 35))
    sev_th = int(_cfg_get(cfg, ["aqm", "severe_threshold"], 75))

    bad_hyst = int(_cfg_get(cfg, ["aqm", "bad_hysteresis"], 5))
    bad_off_th = int(_cfg_get(cfg, ["aqm", "bad_off_threshold"], bad_on_th - bad_hyst))
    bad_off_th = _clamp_bad_off_threshold(bad_off_th, bad_on_th)

    use_cf1 = bool(_cfg_get(cfg, ["aqm", "use_cf1"], True))

    is_bad = False
    last_is_bad: Optional[bool] = None
    oled = _Oled()

    last_pm25: Optional[int] = None
    last_pub_t = time.monotonic()

    log.info(
        "AQM reader running (interval_s=%.3f bad_on=%d bad_off=%d severe=%d "
        "use_cf1=%s win_good=%d win_bad=%d max_win=%d show_values=%s) [RX-only]",
        interval_s,
        bad_on_th,
        bad_off_th,
        sev_th,
        use_cf1,
        win_good,
        win_bad,
        max_win,
        show_values,
    )

    while True:
        frame = await asyncio.to_thread(_find_frame_blocking, ser)
        if frame is None:
            oled.show_waiting()
            await asyncio.sleep(0.1)
            continue

        metrics_raw = _parse_metrics(frame, use_cf1=use_cf1)
        pm1_0_raw = int(metrics_raw["pm1_0"])
        pm25_raw = int(metrics_raw["pm2_5"])
        pm10_raw = int(metrics_raw["pm10"])

        pm1_hist.append(pm1_0_raw)
        pm25_hist.append(pm25_raw)
        pm10_hist.append(pm10_raw)

        # Use heavier filtering when we are currently BAD.
        win_cur = win_bad if is_bad else win_good

        pm1_0 = _avg_last(pm1_hist, win_cur)
        pm25 = _avg_last(pm25_hist, win_cur)
        pm10 = _avg_last(pm10_hist, win_cur)

        now_t = time.monotonic()
        dt = now_t - last_pub_t
        last_pub_t = now_t

        changed = (last_pm25 is None) or (pm25 != last_pm25)
        last_pm25 = pm25

        if show_values:
            log.warning(
                "AQM: dt=%.2fs pm2_5=%d(raw=%d) %s pm1_0=%d(raw=%d) pm10=%d(raw=%d) "
                "win=%d mode=%s",
                dt,
                pm25,
                pm25_raw,
                "CHANGED" if changed else "same",
                pm1_0,
                pm1_0_raw,
                pm10,
                pm10_raw,
                win_cur,
                "BAD" if is_bad else "GOOD",
            )

        await bus.publish(
            Event.now(
                "aqm.metrics",
                "aqm.pms1003",
                pm1_0=pm1_0,
                pm2_5=pm25,
                pm10=pm10,
                pm1_0_raw=pm1_0_raw,
                pm2_5_raw=pm25_raw,
                pm10_raw=pm10_raw,
                filter_window=win_cur,
                filter_window_good=win_good,
                filter_window_bad=win_bad,
            )
        )

        # Hysteresis on FILTERED pm2.5
        if is_bad:
            if pm25 <= bad_off_th:
                is_bad = False
        else:
            if pm25 >= bad_on_th:
                is_bad = True

        severe = pm25 >= sev_th

        if last_is_bad is None or is_bad != last_is_bad:
            await bus.publish(
                Event.now(
                    "aqm.bad" if is_bad else "aqm.good",
                    "aqm.pms1003",
                    pm2_5=pm25,
                    pm2_5_raw=pm25_raw,
                    severe=severe,
                )
            )
            last_is_bad = is_bad

        status = "SEVERE" if severe else ("BAD" if is_bad else "GOOD")
        oled.show(status=status, pm1_0=pm1_0, pm2_5=pm25, pm10=pm10)

        await asyncio.sleep(interval_s)
