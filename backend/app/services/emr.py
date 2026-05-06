import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.visit import Visit
from app.schemas.visit import SOAPNotes, VisitOut

_client = OpenAI(api_key=settings.openai_api_key)


def create_visit(db: Session, patient_id: int) -> dict:
    visit = Visit(patient_id=patient_id)
    db.add(visit)
    db.commit()
    db.refresh(visit)

    return {"success": True, "visit_id": visit.id, "patient_id": visit.patient_id}


def structure_emr(raw_text: str) -> dict:
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a clinical documentation assistant. "
                    "Convert the doctor's raw notes into a structured SOAP format. "
                    "Return a JSON object with keys: subjective, objective, assessment, plan. "
                    "Be concise and medically accurate. Return only valid JSON."
                ),
            },
            {"role": "user", "content": raw_text},
        ],
        response_format={"type": "json_object"},
        temperature=0,
    )

    raw = json.loads(response.choices[0].message.content)

    def to_str(value) -> str:
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            return "; ".join(f"{k}: {v}" for k, v in value.items())
        return str(value)

    soap = SOAPNotes(
        subjective=to_str(raw.get("subjective", "")),
        objective=to_str(raw.get("objective", "")),
        assessment=to_str(raw.get("assessment", "")),
        plan=to_str(raw.get("plan", "")),
    )

    return {
        "success": True,
        "soap_notes": soap.model_dump(),
    }


def save_emr(db: Session, visit_id: int, soap_notes: dict, diagnosis: str | None = None) -> dict:
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        return {"error": f"Visit {visit_id} not found"}

    visit.soap_notes = json.dumps(soap_notes)
    visit.chief_complaint = soap_notes.get("subjective", "")
    if diagnosis:
        visit.diagnosis = diagnosis

    db.commit()
    db.refresh(visit)

    return {"success": True, "visit_id": visit.id, "soap_notes_saved": True}
