import httpx

from app.config import settings

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"


def send_message(chat_id: int | str, text: str) -> dict:
    if not settings.telegram_bot_token:
        return {"error": "Telegram bot token not configured"}

    response = httpx.post(
        f"{TELEGRAM_API}/sendMessage",
        json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
        timeout=10,
    )

    if response.status_code == 200:
        return {"success": True, "chat_id": chat_id}

    return {"error": response.text}


def send_document(chat_id: int | str, file_path: str, caption: str = "") -> dict:
    if not settings.telegram_bot_token:
        return {"error": "Telegram bot token not configured"}

    with open(file_path, "rb") as f:
        response = httpx.post(
            f"{TELEGRAM_API}/sendDocument",
            data={"chat_id": chat_id, "caption": caption},
            files={"document": f},
            timeout=15,
        )

    if response.status_code == 200:
        return {"success": True, "chat_id": chat_id}

    return {"error": response.text}
