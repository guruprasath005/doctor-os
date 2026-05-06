import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

TELEGRAM_API = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
_MAX_TEXT = 4096
_MAX_CAPTION = 1024


def send_message(chat_id: int | str, text: str) -> dict:
    if not settings.telegram_bot_token:
        return {"error": "Telegram bot token not configured"}

    text = text.strip()
    if not text:
        return {"error": "Message text cannot be empty"}

    if len(text) > _MAX_TEXT:
        text = text[: _MAX_TEXT - 3] + "..."

    try:
        response = httpx.post(
            f"{TELEGRAM_API}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
    except httpx.TimeoutException:
        logger.error("Telegram sendMessage timed out for chat_id=[REDACTED]")
        return {"error": "Message delivery timed out"}
    except httpx.RequestError as e:
        logger.error("Telegram sendMessage request error: %s", e)
        return {"error": "Message delivery failed"}

    if response.status_code == 200:
        return {"success": True, "chat_id": chat_id}

    # Markdown parse error — retry as plain text
    if response.status_code == 400:
        try:
            retry = httpx.post(
                f"{TELEGRAM_API}/sendMessage",
                json={"chat_id": chat_id, "text": text},
                timeout=10,
            )
            if retry.status_code == 200:
                return {"success": True, "chat_id": chat_id}
        except httpx.RequestError:
            pass

    logger.error("Telegram sendMessage failed (status %d)", response.status_code)
    return {"error": f"Telegram error {response.status_code}"}


def send_document(chat_id: int | str, file_path: str, caption: str = "") -> dict:
    if not settings.telegram_bot_token:
        return {"error": "Telegram bot token not configured"}

    try:
        with open(file_path, "rb") as f:
            response = httpx.post(
                f"{TELEGRAM_API}/sendDocument",
                data={"chat_id": chat_id, "caption": caption[:_MAX_CAPTION]},
                files={"document": f},
                timeout=30,
            )
    except FileNotFoundError:
        return {"error": f"File not found: {file_path}"}
    except httpx.TimeoutException:
        logger.error("Telegram sendDocument timed out for chat_id=[REDACTED]")
        return {"error": "Document delivery timed out"}
    except httpx.RequestError as e:
        logger.error("Telegram sendDocument request error: %s", e)
        return {"error": "Document delivery failed"}

    if response.status_code == 200:
        return {"success": True, "chat_id": chat_id}

    logger.error("Telegram sendDocument failed (status %d)", response.status_code)
    return {"error": f"Telegram error {response.status_code}"}
