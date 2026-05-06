import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.agent import executor
from app.agent.tools import TOOLS
from app.config import settings

_client = OpenAI(api_key=settings.openai_api_key)

SYSTEM_PROMPT = """
You are an AI assistant for an Indian doctor running a clinic.
You help with patient registration, appointment booking, clinical documentation, and prescriptions.

Guidelines:
- Always search for the patient first before registering — they may already exist.
- Always register the patient if they are new (need name and phone number).
- Always create a visit before recording clinical findings.
- Use structure_emr to convert raw doctor notes into SOAP format, then save_emr.
- Use draft_prescription to generate a prescription, then save_prescription after doctor confirms.
- For appointment bookings: search or register patient first, then create_appointment.
- If information is missing (name, phone, slot time), ask before proceeding.
- Never guess patient details. Only use what is explicitly provided.
- Confirm each completed action with a short, clear message.
- Keep responses brief and professional.
""".strip()


def run(
    user_message: str,
    db: Session,
    conversation_history: list[dict],
    context: dict | None = None,
) -> str:
    conversation_history.append({"role": "user", "content": user_message})

    messages = [{"role": "system", "content": SYSTEM_PROMPT}] + conversation_history

    while True:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=TOOLS,
            tool_choice="auto",
            temperature=0,
        )

        choice = response.choices[0]
        message = choice.message

        messages.append(message)

        if choice.finish_reason == "tool_calls" and message.tool_calls:
            for tool_call in message.tool_calls:
                result = executor.dispatch(
                    tool_name=tool_call.function.name,
                    arguments=tool_call.function.arguments,
                    db=db,
                    context=context,
                )
                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(result),
                    }
                )
        else:
            reply = message.content or ""
            conversation_history.append({"role": "assistant", "content": reply})
            return reply
