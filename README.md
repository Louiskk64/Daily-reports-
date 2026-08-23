# Daily-reports — Imou + Shine Smart starter

Monitors an Imou camera for motion/intrusion and sends daily solar
production reports from the Shine Smart (Growatt) app to WhatsApp via
Twilio.

**Important:** this repo contains templates and placeholders only.
Never commit real credentials — use `config.yml` (gitignored) locally,
and GitHub Secrets / environment variables in CI or production.

## Files

- `imou_cloud.py` — Imou Open Platform client (snapshot + motion events)
- `solar_shine.py` — Shine Smart (Growatt) plant data client
- `notifier/twilio_whatsapp.py` — Twilio WhatsApp sender
- `monitor.py` — continuous loop polling the camera, alerts on motion
- `scheduler.py` — sends the daily solar report at a configured time
- `config.example.yml` — copy to `config.yml` and fill in real values
- `Dockerfile` + `docker-compose.yml` — run monitor & scheduler as services
- `requirements.txt`

## Setup

### 1. Imou Open Platform account
Register a developer account and app at https://open.imoulife.com/ (this
is separate from your normal Imou Life login). Bind your camera to the
app and note the App ID, App Secret, and device ID.

### 2. Shine Smart / Growatt credentials
Use the same username/password you log into the ShinePhone app with, and
find your `plant_id` from the plant URL in the app or ShineServer web
portal.

### 3. Twilio WhatsApp
1. Create a free account at https://www.twilio.com/try-twilio
2. In the Twilio console: Messaging → Try it out → Send a WhatsApp message
3. From your own WhatsApp, send the shown join code to the sandbox number
4. Copy your Account SID and Auth Token from the console dashboard

### 4. Configure
```bash
cp config.example.yml config.yml
# edit config.yml with the values collected above
```

### 5. Run locally
```bash
pip install -r requirements.txt
python monitor.py      # in one terminal
python scheduler.py    # in another
```

### 6. Or run with Docker
```bash
docker compose up --build -d
docker compose logs -f
```

## Notes / known limitations

- The Shine/Growatt client uses the same unofficial session-based
  endpoints the ShinePhone app uses internally — Growatt doesn't publish
  a public API for individual accounts, so field names in the response
  may need adjusting; run `python solar_shine.py` standalone to inspect
  the raw response and confirm parsing.
- The Imou client's action names follow the published Imou Open API
  conventions but should be double-checked against current docs before
  relying on this for real security alerts.
- `monitor.py` alerts are deduplicated by `alarmId` with a cooldown
  window (default 5 min) to avoid WhatsApp spam on repeated motion.
