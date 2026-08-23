"""
imou_cloud.py — Template client for the Imou Open Platform (openapi.easy4ip.com).

Requires a native Imou "Open Platform" developer account (separate from your
regular Imou Life app login): https://open.imoulife.com/
Register an app there to get an App ID + App Secret, and bind your camera's
device ID to that app.

NOTE: Imou's Open API uses action-based endpoints with a signed request body
(HMAC-SHA256 over sorted params + app_secret). The exact action names below
(accessToken.get, device.deviceBaseList.get, device.snap.get) reflect Imou's
published API conventions as of this writing — verify the current action
names and required params against the latest Imou Open API docs before
relying on this in production, as third-party platform APIs change.

This module intentionally has no live credentials and will not run until
you fill in config.yml.
"""
import hashlib
import time
import uuid
import requests


class ImouCloudClient:
    def __init__(self, app_id: str, app_secret: str, api_base: str):
        self.app_id = app_id
        self.app_secret = app_secret
        self.api_base = api_base.rstrip("/")
        self._token = None
        self._token_expires_at = 0

    # ---- internal helpers -------------------------------------------------

    def _sign(self, params: dict) -> str:
        """Build the signature Imou expects: sorted key=value pairs + app_secret, sha256."""
        ordered = sorted(params.items())
        raw = "&".join(f"{k}={v}" for k, v in ordered) + f"&{self.app_secret}"
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()

    def _post(self, action: str, params: dict) -> dict:
        body = {
            "system": {
                "ver": "1.0",
                "sign": "",
                "appId": self.app_id,
                "time": int(time.time()),
                "nonce": uuid.uuid4().hex,
            },
            "params": params,
            "id": uuid.uuid4().hex,
        }
        body["system"]["sign"] = self._sign(
            {
                "time": body["system"]["time"],
                "nonce": body["system"]["nonce"],
                "appId": self.app_id,
                "appSecret": self.app_secret,
            }
        )
        url = f"{self.api_base}/{action}"
        resp = requests.post(url, json=body, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        if data.get("result", {}).get("code") not in (None, "0", 0):
            raise RuntimeError(f"Imou API error on {action}: {data}")
        return data.get("result", {}).get("data", {})

    # ---- public methods -----------------------------------------------------

    def get_access_token(self) -> str:
        """Fetch (and cache) an access token. Tokens are typically valid ~24h."""
        if self._token and time.time() < self._token_expires_at - 60:
            return self._token
        data = self._post("accessToken.get", {})
        self._token = data.get("accessToken")
        self._token_expires_at = time.time() + int(data.get("expireTime", 86400))
        if not self._token:
            raise RuntimeError("Failed to obtain Imou access token")
        return self._token

    def get_snapshot_url(self, device_id: str, channel_id: str = "0") -> str:
        """Request a fresh snapshot image URL from the camera."""
        self.get_access_token()
        data = self._post(
            "device.snap.get",
            {"deviceId": device_id, "channelId": channel_id},
        )
        snap_url = data.get("url")
        if not snap_url:
            raise RuntimeError(f"No snapshot URL returned for device {device_id}")
        return snap_url

    def get_recent_motion_events(self, device_id: str, channel_id: str = "0", limit: int = 5) -> list:
        """Return recent motion/alarm events for a device, most recent first."""
        self.get_access_token()
        data = self._post(
            "device.alarm.list.get",
            {"deviceId": device_id, "channelId": channel_id, "pageSize": limit},
        )
        return data.get("alarms", [])


if __name__ == "__main__":
    # Quick manual smoke test — fill config.yml first.
    import yaml

    with open("config.yml") as f:
        cfg = yaml.safe_load(f)["imou"]

    client = ImouCloudClient(cfg["app_id"], cfg["app_secret"], cfg["api_base"])
    print("Access token:", client.get_access_token()[:12], "...")
    print("Snapshot URL:", client.get_snapshot_url(cfg["device_id"], cfg["channel_id"]))
