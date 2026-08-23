"""
notifier/twilio_whatsapp.py — Send WhatsApp messages via Twilio.

Setup:
1. Create a Twilio account: https://www.twilio.com/try-twilio
2. For quick testing, join the Twilio WhatsApp Sandbox from your console
   (Messaging > Try it out > Send a WhatsApp message) and send the join
   code from your WhatsApp to the sandbox number shown there.
3. Grab your Account SID and Auth Token from the Twilio console dashboard.
4. Put them, the sandbox "from" number, and your own WhatsApp number
   (E.164 format, e.g. +91XXXXXXXXXX) into config.yml.

For production use beyond the sandbox, you'd apply for a WhatsApp Business
sender through Twilio, which is a separate approval process.
"""
from twilio.rest import Client


class TwilioWhatsAppNotifier:
    def __init__(self, account_sid: str, auth_token: str, from_whatsapp: str, to_whatsapp: str):
        self.client = Client(account_sid, auth_token)
        self.from_whatsapp = from_whatsapp
        self.to_whatsapp = to_whatsapp

    def send(self, message: str) -> str:
        """Send a WhatsApp message, return the Twilio message SID."""
        msg = self.client.messages.create(
            body=message,
            from_=self.from_whatsapp,
            to=self.to_whatsapp,
        )
        return msg.sid


if __name__ == "__main__":
    import yaml

    with open("../config.yml") as f:
        cfg = yaml.safe_load(f)["twilio"]

    notifier = TwilioWhatsAppNotifier(
        cfg["account_sid"], cfg["auth_token"], cfg["from_whatsapp"], cfg["to_whatsapp"]
    )
    sid = notifier.send("Test message from daily-reports setup.")
    print("Sent, SID:", sid)
