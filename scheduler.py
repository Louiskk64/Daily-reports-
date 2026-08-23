"""
scheduler.py — Send a daily solar production report over WhatsApp at a
configured time (default 19:00 server time). Runs forever; check the
container/host timezone matches what you expect for "19:00".
"""
import time
import logging
import schedule
import yaml

from solar_shine import ShineSmartClient
from notifier.twilio_whatsapp import TwilioWhatsAppNotifier

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
log = logging.getLogger("scheduler")


def load_config(path: str = "config.yml") -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def send_daily_report(shine: ShineSmartClient, notifier: TwilioWhatsAppNotifier):
    try:
        report = shine.get_daily_report()
        message = (
            f"☀️ Daily Solar Report — {report['plant_name']}\n"
            f"Today: {report['energy_today_kwh']} kWh\n"
            f"Total lifetime: {report['energy_total_kwh']} kWh\n"
            f"Current output: {report['current_power_w']} W"
        )
        notifier.send(message)
        log.info("Daily report sent successfully")
    except Exception as exc:  # noqa: BLE001 — don't crash the scheduler
        log.error("Failed to send daily report: %s", exc)


def main():
    cfg = load_config()
    shine_cfg = cfg["shine"]
    twilio_cfg = cfg["twilio"]
    report_time = cfg.get("scheduler", {}).get("daily_report_time", "19:00")

    shine = ShineSmartClient(
        shine_cfg["username"], shine_cfg["password"], shine_cfg["plant_id"], shine_cfg["api_base"]
    )
    notifier = TwilioWhatsAppNotifier(
        twilio_cfg["account_sid"],
        twilio_cfg["auth_token"],
        twilio_cfg["from_whatsapp"],
        twilio_cfg["to_whatsapp"],
    )

    schedule.every().day.at(report_time).do(send_daily_report, shine=shine, notifier=notifier)
    log.info("Scheduler started — daily report will send at %s", report_time)

    while True:
        schedule.run_pending()
        time.sleep(30)


if __name__ == "__main__":
    main()
