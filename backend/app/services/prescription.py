import json

from openai import OpenAI
from sqlalchemy.orm import Session

from app.config import settings
from app.models.prescription import Prescription
from app.schemas.prescription import Drug

_client = OpenAI(api_key=settings.openai_api_key)


def draft_prescription(symptoms: str, diagnosis: str) -> dict:
    response = _client.chat.completions.create(
        model="gpt-4o-mini",
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a clinical prescription assistant for an Indian doctor. "
                    "Based on symptoms and diagnosis, draft a prescription. "
                    "Return a JSON object with key 'drugs' containing a list of drug objects. "
                    "Each drug object must have: name, dosage, frequency, duration, instructions. "
                    "Use standard Indian generic drug names. Return only valid JSON."
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

    content = json.loads(response.choices[0].message.content)
    drugs = [Drug.model_validate(d) for d in content.get("drugs", [])]

    return {
        "success": True,
        "drugs": [d.model_dump() for d in drugs],
    }


def save_prescription(db: Session, visit_id: int, drugs: list[dict], instructions: str | None = None) -> dict:
    prescription = Prescription(
        visit_id=visit_id,
        drugs=json.dumps(drugs),
        instructions=instructions,
    )
    db.add(prescription)
    db.commit()
    db.refresh(prescription)

    return {
        "success": True,
        "prescription_id": prescription.id,
        "visit_id": prescription.visit_id,
        "drugs_count": len(drugs),
    }
