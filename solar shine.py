"""
solar_shine.py — Template client for the "Shine" solar monitoring portal
(Growatt ShineServer / ShinePhone app, server.growatt.com).

Growatt does not publish an official public API for individual users —
this uses the same session-based login + plant-data endpoints that the
ShinePhone mobile app and Sunny web portal use internally. These are
unofficial and can change without notice; if requests start failing,
check for updated endpoint paths (community Growatt API wrappers are a
good reference point) before assuming your credentials are wrong.

If your installation actually uses a different monitoring brand (SMA
Sunny Portal, SolarEdge, Solis, etc.) desps, swap this module out for
that provider's client — the rest of the pipeline (scheduler.py calling
get_daily_report()) doesn't care which brand it talks to.
"""
import hashlib
import requests


class ShineSmartClient:
    def __init__(self, username: str, password: str, plant_id: str, api_base: str):
        self.username = username
        self.password = password
        self.plant_id = plant_id
        self.api_base = api_base.rstrip("/")
        self.session = requests.Session()
        self._logged_in = False

    def _md5(self, text: str) -> str:
        return hashlib.md5(text.encode("utf-8")).hexdigest()

    def login(self):
        if self._logged_in:
            return
        resp = self.session.post(
            f"{self.api_base}/login",
            data={
                "account": self.username,
                "password": self._md5(self.password),
                "validateCode": "",
            },
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
        if not data.get("success", data.get("result") == 1):
            raise RuntimeError(f"Shine login failed: {data}")
        self._logged_in = True

    def get_plant_summary(self) -> dict:
        """Return today's key production figures for the configured plant."""
        self.login()
        resp = self.session.post(
            f"{self.api_base}/panel/getDevicesByPlantList",
            data={"plantId": self.plant_id, "currPage": 1},
            timeout=15,
        )
        resp.raise_for_status()
        return resp.json()

    def get_daily_report(self) -> dict:
        """
        Return a normalized summary for today's report:
        {energy_today_kwh, energy_total_kwh, current_power_w, plant_name}
        Field names below follow Growatt's typical response shape —
        confirm against a real logged-in response and adjust the parsing
        if your account's payload differs.
        """
        raw = self.get_plant_summary()
        plant_data = raw.get("obj", raw.get("data", {}))
        return {
            "plant_name": plant_data.get("plantName", "Solar Plant"),
            "energy_today_kwh": plant_data.get("todayEnergy", "N/A"),
            "energy_total_kwh": plant_data.get("totalEnergy", "N/A"),
            "current_power_w": plant_data.get("currentPower", "N/A"),
        }


if __name__ == "__main__":
    import yaml

    with open("config.yml") as f:
        cfg = yaml.safe_load(f)["shine"]

    client = ShineSmartClient(cfg["username"], cfg["password"], cfg["plant_id"], cfg["api_base"])
    print(client.get_daily_report())
