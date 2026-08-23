# Daily-reports - Imou + Shine Smart starter

This repository contains a starter implementation to monitor an Imou camera (via Imou cloud/native account) for intrusions and send daily solar production reports from the Shine Smart app to WhatsApp using Twilio.

Important: this starter contains templates and placeholders only. Do NOT commit credentials. Use environment variables or GitHub secrets.

Files added:
- imou_cloud.py — Imou cloud client template (native Imou account required)
- solar_shine.py — Shine Smart scraper / API template
- notifier/twilio_whatsapp.py — Twilio WhatsApp sender
- monitor.py — continuous monitor that polls camera snapshots and sends alerts on motion
- scheduler.py — schedules daily Shine Smart report at 19:00
- config.example.yml — example config file
- Dockerfile + docker-compose.yml — run both monitor & scheduler
- requirements.txt
- README.md — setup steps (create native Imou account, Twilio sandbox, env vars)

Please fill the environment variables listed in README.md before running.
