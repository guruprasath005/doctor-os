import json
import logging

from openai import OpenAI, OpenAIError
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.models.prescription import Prescription
from app.models.visit import Visit
from app.schemas.prescription import Drug

logger = logging.getLogger(__name__)

_client = OpenAI(api_key=settings.openai_api_key)


def draft_prescription(symptoms: str, diagnosis: str) -> dict:
    try:
        response = _client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a clinical prescription assistant for an Indian doctor. "
                        "Based on symptoms and diagnosis, draft a prescription using standard Indian generic drug names. "
                        "Return a JSON object with key 'drugs' — a list of drug objects. "
                        "Each drug must have: name (string), dosage (string, e.g. '500mg'), "
                        "frequency (string, e.g. 'Twice daily'), duration (string, e.g. '5 days'), "
                        "instructions (string, optional). "
                        "All values must be plain strings. Return only valid JSON."
                    ),
                },
                {
                    "role": "user",
                    "content": f"Symptoms: {symptoms}\nDiagnosis: {diagnosis}",
                },
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
    except OpenAIError as e:
        logger.error("OpenAI API error in draft_prescription: %s", e)
        return {"error": "Unable to draft prescription right now. Please try again."}

    content = json.loads(response.choices[0].message.content)
    raw_drugs = content.get("drugs", [])

    if not raw_drugs:
        return {"error": "No drugs were generated for the given symptoms and diagnosis"}

    drugs = []
    for d in raw_drugs:
        try:
            drugs.append(Drug.model_validate(d))
        except ValidationError:
            continue

    if not drugs:
        return {"error": "Could not parse any valid drug entries from the model response"}

    return {"success": True, "drugs": [d.model_dump() for d in drugs]}


def save_prescription(
    db: Session, visit_id: int, drugs: list[dict], instructions: str | None = None
) -> dict:
    visit = db.query(Visit).filter(Visit.id == visit_id).first()
    if not visit:
        return {"error": f"Visit {visit_id} not found"}

    existing = db.query(Prescription).filter(Prescription.visit_id == visit_id).first()
    if existing:
        return {
            "already_saved": True,
            "prescription_id": existing.id,
            "visit_id": visit_id,
            "message": f"Prescription #{existing.id} already exists for this visit.",
        }

    validated = []
    for d in drugs:
        try:
            validated.append(Drug.model_validate(d).model_dump())
        except ValidationError as e:
            return {"error": f"Invalid drug entry: {e.errors()[0]['msg']}"}

    prescription = Prescription(
        visit_id=visit_id,
        drugs=json.dumps(validated),
        instructions=instructions.strip() if instructions else None,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    return {
        "success": True,
        "prescription_id": prescription.id,
        "visit_id": prescription.visit_id,
        "drugs_count": len(validated),
    }
