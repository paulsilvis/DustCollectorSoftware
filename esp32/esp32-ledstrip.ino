#include <FastLED.h>

// ===== CONFIG =====
#define DATA_PIN        4
#define LED_TYPE        WS2812B
#define COLOR_ORDER     GRB
#define NUM_LEDS        600
#define BRIGHTNESS      48

#define BLOB_LEN        8    // set to 10 or 15 if you like
#define GAP_LEN         30   // blank LEDs between blobs
#define STEP_DELAY_MS   10   // lower = faster
#define DIRECTION       +1   // +1 = near->far, -1 = far->near

// ---- Optional fade controls ----
// Set EDGE_FADE_PIXELS = 0 to disable fade
#define EDGE_FADE_PIXELS  0  //3
#define EDGE_MIN_SCALE    64 // 0..255 brightness at the very edge

// ===== ON/OFF CONTROL (from Pi) =====
#define CONTROL_PIN      16  // ESP32 GPIO16 (connect to Pi GPIO5 via 3.3V logic)
                             // Use INPUT_PULLDOWN so default = OFF

CRGB leds[NUM_LEDS];
static int phase = 0;

inline CRGB fadeColorAt(const CRGB& base, int posInBlob) {
  if (EDGE_FADE_PIXELS <= 0) return base;

  int d = posInBlob < (BLOB_LEN - 1 - posInBlob) ? posInBlob : (BLOB_LEN - 1 - posInBlob);
  if (d >= EDGE_FADE_PIXELS) return base;

  uint8_t scale = (EDGE_FADE_PIXELS <= 1)
                    ? EDGE_MIN_SCALE
                    : (uint8_t)(EDGE_MIN_SCALE +
                        ((255 - EDGE_MIN_SCALE) * d) / (EDGE_FADE_PIXELS - 1));

  CRGB c = base;
  c.nscale8_video(scale);
  return c;
}

inline CRGB colorFor(uint16_t t) {
  const uint16_t segment = BLOB_LEN + GAP_LEN;

  if (t < BLOB_LEN) {                 // RED segment
    return fadeColorAt(CRGB::Red, t);
  }
  if (t < segment) return CRGB::Black;

  t -= segment;                        // GREEN segment
  if (t < BLOB_LEN) {
    return fadeColorAt(CRGB::Green, t);
  }
  if (t < segment) return CRGB::Black;

  t -= segment;                        // BLUE segment
  if (t < BLOB_LEN) {
    return fadeColorAt(CRGB::Blue, t);
  }
  return CRGB::Black;
}

void drawFrame() {
  const uint16_t cycle = 3 * (BLOB_LEN + GAP_LEN);
  for (int i = 0; i < NUM_LEDS; ++i) {
    int32_t u = (int32_t)i + (int32_t)DIRECTION * phase;
    uint16_t t = (uint16_t)((u % cycle + cycle) % cycle);  // positive modulo
    leds[i] = colorFor(t);
  }
  FastLED.show();
}

void setup() {
  pinMode(CONTROL_PIN, INPUT_PULLDOWN);  // default OFF until Pi drives HIGH
  FastLED.addLeds<LED_TYPE, DATA_PIN, COLOR_ORDER>(leds, NUM_LEDS);
  FastLED.setBrightness(BRIGHTNESS);
  FastLED.clear(true);
}

void loop() {
  static int last_state = -1;  // -1 = unknown, 0 = off, 1 = on
  const int state = digitalRead(CONTROL_PIN);

  // Edge handling: clear once on transition to OFF
  if (state != last_state) {
    last_state = state;
    if (state == LOW) {
      FastLED.clear(true);   // immediately blank the strip
    }
  }

  if (state == HIGH) {
    drawFrame();
    const uint16_t cycle = 3 * (BLOB_LEN + GAP_LEN);
    phase = (phase + 1) % cycle;
    delay(STEP_DELAY_MS);
  } else {
    delay(5);  // idle while OFF
  }
}
