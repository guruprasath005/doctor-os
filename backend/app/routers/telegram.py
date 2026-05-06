import logging

from fastapi import APIRouter, Header, HTTPException, Request

from app.agent import brain
from app.config import settings
from app.database import SessionLocal
from app.services.messenger import send_message

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/webhook", tags=["telegram"])

_conversation_store: dict[str, list[dict]] = {}
_MAX_HISTORY = 40  # 20 user+assistant pairs


@router.post("/telegram")
def telegram_webhook(
    request: Request,
    update: dict,
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if settings.telegram_webhook_secret:
        if x_telegram_bot_api_secret_token != settings.telegram_webhook_secret:
            raise HTTPException(status_code=403, detail="Invalid webhook secret")

    message = update.get("message") or update.get("edited_message")
    if not message:
        return {"ok": True}

    chat_id = str(message["chat"]["id"])
    text = message.get("text", "").strip()

    if not text:
        return {"ok": True}

    if text.startswith("/start"):
        send_message(chat_id, "Welcome to the clinic assistant. How can I help you today?")
        return {"ok": True}

    if text.startswith("/new"):
        _conversation_store.pop(chat_id, None)
        send_message(chat_id, "Session cleared. How can I help you?")
        return {"ok": True}

    if text.startswith("/help"):
        send_message(
            chat_id,
            "I can help you with:\n"
            "- Register patients\n"
            "- Book appointments\n"
            "- Record clinical notes\n"
            "- Draft prescriptions\n"
            "- Check today's queue\n\n"
            "Type /new to clear the current session.",
        )
        return {"ok": True}

    history = _conversation_store.setdefault(chat_id, [])

    if len(history) > _MAX_HISTORY:
        history[:] = history[-_MAX_HISTORY:]

    db = SessionLocal()
    try:
        reply = brain.run(
            user_message=text,
            db=db,
            conversation_history=history,
            context={"chat_id": chat_id},
        )
        send_message(chat_id, reply)
    except Exception:
        logger.exception("Unhandled error processing Telegram message (chat_id redacted)")
        send_message(chat_id, "Something went wrong. Please try again or type /new to reset.")
    finally:
        db.close()

    return {"ok": True}
