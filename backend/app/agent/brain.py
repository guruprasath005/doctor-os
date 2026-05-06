import json
import logging
from datetime import date

from openai import OpenAI, OpenAIError
from sqlalchemy.orm import Session

from app.agent import executor
from app.agent.tools import TOOLS
from app.config import settings

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=settings.openai_api_key)

_MAX_TURNS = 10
_MAX_HISTORY = 40  # 20 user+assistant pairs

_SYSTEM_PROMPT = """
You are an AI assistant for an Indian doctor running a clinic.
You help with patient registration, appointment booking, clinical documentation, and prescriptions.
Today's date is {today}.

Workflow rules (follow in order):
1. ALWAYS call search_patient before register_patient — check if the patient exists first.
2. Register only if not found. Ask for name and phone if missing.
3. ALWAYS call create_visit before save_emr or draft_prescription.
4. Call structure_emr on raw notes, then immediately call save_emr with the result.
5. Call draft_prescription, show the drug list to the doctor for confirmation, then call save_prescription.
6. For bookings: search/register patient → create_appointment. Slot must be a future date/time.
7. Default doctor_id is 1 unless specified. Slot format: YYYY-MM-DD HH:MM (24-hour).
8. Never guess or invent patient details. Ask if anything is missing.
9. When a tool returns a patient name, ALWAYS use that name in your reply — never use the name the user typed.
10. For rescheduling: you need the full new date AND time. If the user gives only a time (e.g. "to 12:00 PM") without a new date, ask "Which date should the new appointment be on?" before calling any tool.
11. Respond in plain text only — no markdown, no asterisks, no bullet symbols.
12. Keep all replies short and professional.
""".strip()


def run(
    user_message: str,
    db: Session,
    conversation_history: list[dict],
    context: dict | None = None,
) -> str:
    if len(conversation_history) > _MAX_HISTORY:
        conversation_history[:] = conversation_history[-_MAX_HISTORY:]

    conversation_history.append({"role": "user", "content": user_message})

    system = _SYSTEM_PROMPT.format(today=date.today().isoformat())
    messages = [{"role": "system", "content": system}] + conversation_history

    for _ in range(_MAX_TURNS):
        try:
            response = _client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                temperature=0,
            )
        except OpenAIError as e:
            logger.error("OpenAI API error in brain.run: %s", e)
            return "I'm having trouble connecting right now. Please try again in a moment."

        choice = response.choices[0]
        message = choice.message
        messages.append(message)

        if choice.finish_reason == "tool_calls" and message.tool_calls:
            for tool_call in message.tool_calls:
                try:
                    result = executor.dispatch(
                        tool_name=tool_call.function.name,
                        arguments=tool_call.function.arguments,
                        db=db,
                        context=context,
                    )
                except Exception as e:
                    logger.error("Tool error [%s]: %s", tool_call.function.name, e)
                    result = {"error": "An internal error occurred while executing this action."}

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

    logger.warning("Agent reached max turns (%d) without completing", _MAX_TURNS)
    return "I wasn't able to complete that. Please try breaking it into smaller steps."
