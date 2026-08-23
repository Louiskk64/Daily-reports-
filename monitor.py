"""
monitor.py — Poll the Imou camera for motion events and send a WhatsApp
alert (via Twilio) when new motion is detected. Runs forever; intended to
be run under Docker/systemd/etc. so it restarts on crash.
"""
import time
import logging
import yaml

from imou_cloud import ImouCloudClient
from notifier.twilio_whatsapp import TwilioWhatsAppNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("monitor")


def load_config(path: str = "config.yml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def main():
    cfg = load_config()
    imou_cfg = cfg["imou"]
    twilio_cfg = cfg["twilio"]
    mon_cfg = cfg.get("monitor", {})

    poll_interval = int(mon_cfg.get("poll_interval_seconds", 60))
    cooldown = int(mon_cfg.get("alert_cooldown_seconds", 300))

    imou = ImouCloudClient(imou_cfg["app_id"], imou_cfg["app_secret"], imou_cfg["api_base"])
    notifier = TwilioWhatsAppNotifier(
        twilio_cfg["account_sid"],
        twilio_cfg["auth_token"],
        twilio_cfg["from_whatsapp"],
        twilio_cfg["to_whatsapp"],
    )

    seen_event_ids = set()
    last_alert_time = 0

    log.info("Starting camera monitor (poll every %ss)", poll_interval)

    while True:
        try:
            events = imou.get_recent_motion_events(
                imou_cfg["device_id"], imou_cfg["channel_id"], limit=5
            )
            new_events = [e for e in events if e.get("alarmId") not in seen_event_ids]

            if new_events and (time.time() - last_alert_time) > cooldown:
                latest = new_events[0]
                seen_event_ids.update(e.get("alarmId") for e in new_events)
                message = (
                    f"⚠️ Motion detected on camera\n"
                    f"Time: {latest.get('alarmTime', 'unknown')}\n"
                    f"Type: {latest.get('alarmType', 'motion')}"
                )
                notifier.send(message)
                last_alert_time = time.time()
                log.info("Alert sent for event %s", latest.get("alarmId"))
            elif new_events:
                log.info("New motion event(s) detected but within cooldown window; skipping alert")
                seen_event_ids.update(e.get("alarmId") for e in new_events)

        except Exception as exc:  # noqa: BLE001 — keep the loop alive
            log.error("Error during poll cycle: %s", exc)

        time.sleep(poll_interval)


if __name__ == "__main__":
    main()
