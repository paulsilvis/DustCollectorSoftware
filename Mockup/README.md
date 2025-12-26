# DustCollector — asyncio single-queue event bus (skeleton)

This is a runnable skeleton for the dust collector controller on a Raspberry Pi 4B.
- Debian 12 (Bookworm), Python 3.11
- Single in-process `asyncio.Queue` event bus
- No collector tail (OFF immediately when none active)
- PMS1003 & ESP32 share UART0 @ 9600 bps (RX for PMS, TX for ESP32)
- I²C devices: LCD2004 (0x3F), SSD1306 (0x3C), ADS1115 (0x48), PCF8574s 0x20–0x24

## Quick start
```bash
cd ~/dustcollector
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python -m src.main --config config/config.yaml
```
To install as a service:
```bash
sudo cp system/dustcollector.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now dustcollector
```

## Notes
- Outputs default safe at boot and on crash.
- Gate controller enforces no FWD+REV and direction dead-time.
- Replace stub hardware drivers with your working code as desired.


## Run on a laptop (mock mode)
Set `system.mock: true` in `config/config.yaml` and run:

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
python -m src.main --config config/config.yaml
```

Expected: simulated tool on/off edges, gate open/close logs, collector ON/OFF,
and periodic AQM good/bad events.

## Mock mode selection (IMPORTANT)
You can enable mock mode in either of two ways:

1) Edit config:
```yaml
system:
  mock: true
```

2) Or (no edits) set an environment override:
```bash
export MOCK=true
```

### Use the venv's Python (avoids Anaconda hijacking)
After activating the venv, you can still force the right interpreter with:

```bash
. .venv/bin/activate
.venv/bin/python -m src.main --config config/config.yaml
```

### Event delivery semantics
This project uses an `EventBus` (fan-out). Every task sees every event. We do NOT
use a single shared `asyncio.Queue`, because that is a work queue (one consumer)
and causes confusing, nondeterministic behavior.


### Quickstart
```bash
chmod +x install.sh run.sh
./install.sh
./run.sh
```
