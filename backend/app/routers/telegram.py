from fastapi import APIRouter, Header, HTTPException, Request

from app.agent import brain
from app.config import settings
from app.database import SessionLocal
from app.services.messenger import send_message

router = APIRouter(prefix="/webhook", tags=["telegram"])

_conversation_store: dict[str, list[dict]] = {}


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

    if text == "/start":
        send_message(chat_id, "Welcome to the clinic. How can I help you today?")
        return {"ok": True}

    if text == "/new":
        _conversation_store.pop(chat_id, None)
        send_message(chat_id, "Session cleared. How can I help you?")
        return {"ok": True}

    history = _conversation_store.setdefault(chat_id, [])
    db = SessionLocal()

    try:
        reply = brain.run(
            user_message=text,
            db=db,
            conversation_history=history,
            context={"chat_id": chat_id},
        )
        send_message(chat_id, reply)
    except Exception as e:
        send_message(chat_id, "Something went wrong. Please try again.")
        raise e
    finally:
        db.close()

    return {"ok": True}
