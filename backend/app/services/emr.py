import json
import logging

from openai import OpenAI, OpenAIError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.patient import Patient
from app.models.visit import Visit
from app.schemas.visit import SOAPNotes

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=settings.openai_api_key)


def create_visit(db: Session, patient_id: int) -> dict:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {"error": f"Patient {patient_id} not found"}

    open_visit = (
        db.query(Visit)
        .filter(Visit.patient_id == patient_id, Visit.closed_at.is_(None))
        .first()
    )
    if open_visit:
        return {
            "already_open": True,
            "visit_id": open_visit.id,
            "patient_id": patient_id,
            "message": f"Open visit #{open_visit.id} already exists for {patient.name}. Use this visit_id.",
        }

    visit = Visit(patient_id=patient_id)
    db.add(visit)
    db.commit()
    db.refresh(visit)

    return {"success": True, "visit_id": visit.id, "patient_id": visit.patient_id}


def structure_emr(raw_text: str) -> dict:
    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a clinical documentation assistant. "
                        "Convert the doctor's raw notes into a structured SOAP format. "
                        "Return a JSON object with exactly these four string keys: "
                        "subjective, objective, assessment, plan. "
                        "Each value must be a plain string — no nested objects or lists. "
                        "Be concise and medically accurate."
                    ),
                },
                {"role": "user", "content": raw_text},
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except OpenAIError as e:
        logger.error("OpenAI API error in structure_emr: %s", e)
        return {"error": "Unable to structure notes right now. Please try again."}

    raw = json.loads(response.choices[0].message.content)

    def to_str(value) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            return "; ".join(f"{k}: {v}" for k, v in value.items())
        if isinstance(value, list):
            return "; ".join(str(item) for item in value)
        return str(value)

    soap = SOAPNotes(
        subjective=to_str(raw.get("subjective", "")),
        objective=to_str(raw.get("objective", "")),
        assessment=to_str(raw.get("assessment", "")),
        plan=to_str(raw.get("plan", "")),
    )

    return {"success": True, "soap_notes": soap.model_dump()}


def save_emr(db: Session, visit_id: int, soap_notes: dict, diagnosis: str | None = None) -> dict:
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        return {"error": f"Visit {visit_id} not found"}

    if visit.closed_at is not None:
        return {"error": f"Visit {visit_id} is already closed"}

    required_keys = {"subjective", "objective", "assessment", "plan"}
    missing = required_keys - set(soap_notes.keys())
    if missing:
        return {"error": f"soap_notes missing required fields: {', '.join(sorted(missing))}"}

    def to_str(value) -> str:
        if isinstance(value, str):
            return value.strip()
        if isinstance(value, dict):
            return "; ".join(f"{k}: {v}" for k, v in value.items())
        return str(value)

    cleaned = {k: to_str(soap_notes[k]) for k in required_keys}

    visit.soap_notes = json.dumps(cleaned)
    visit.chief_complaint = cleaned.get("subjective", "")
    if diagnosis and str(diagnosis).strip():
        visit.diagnosis = str(diagnosis).strip()

    db.commit()
    db.refresh(visit)

    return {"success": True, "visit_id": visit.id, "soap_notes_saved": True}
