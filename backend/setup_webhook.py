"""
Run this script after starting ngrok to register the Telegram webhook.

Usage:
    python3 setup_webhook.py <ngrok-https-url>

Example:
    python3 setup_webhook.py https://abc123.ngrok-free.app
"""

import sys
import httpx
from app.config import settings


def register_webhook(ngrok_url: str):
    webhook_url = f"{ngrok_url.rstrip('/')}/webhook/telegram"

    payload = {"url": webhook_url}
    if settings.telegram_webhook_secret:
        payload["secret_token"] = settings.telegram_webhook_secret

    response = httpx.post(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/setWebhook",
        json=payload,
        timeout=10,
    )

    data = response.json()
    if data.get("ok"):
        print(f"Webhook registered: {webhook_url}")
    else:
        print(f"Failed: {data}")


def get_webhook_info():
    response = httpx.get(
        f"https://api.telegram.org/bot{settings.telegram_bot_token}/getWebhookInfo",
        timeout=10,
    )
    print("Current webhook info:", response.json())


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        get_webhook_info()
        sys.exit(0)

    register_webhook(sys.argv[1])
