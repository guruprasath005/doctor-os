from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientOut


def register_patient(db: Session, data: PatientCreate | dict) -> dict:
    if isinstance(data, dict):
        try:
            data = PatientCreate(**data)
        except ValidationError as e:
            errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
            return {"error": "; ".join(errors)}

    existing = db.query(Patient).filter(Patient.phone == data.phone).first()
    if existing:
        return {
            "already_registered": True,
            "patient_id": existing.id,
            "name": existing.name,
            "phone": existing.phone,
            "message": f"{existing.name} is already registered. Using existing record.",
        }

    patient = Patient(
        name=data.name,
        phone=data.phone,
        dob=data.dob,
        gender=data.gender,
        consent_given=data.consent_given,
    )
    db.add(patient)
    db.commit()
    db.refresh(patient)

    return {
        "success": True,
        "patient_id": patient.id,
        "name": patient.name,
        "phone": patient.phone,
    }


def get_patient(db: Session, patient_id: int) -> dict:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {"error": f"Patient {patient_id} not found"}

    return PatientOut.model_validate(patient).model_dump(mode="json")


def search_patient(db: Session, query: str) -> dict:
    results = (
        db.query(Patient)
        .filter(
            (Patient.name.ilike(f"%{query}%")) | (Patient.phone.ilike(f"%{query}%"))
        )
        .limit(5)
        .all()
    )

    if not results:
        return {"found": False, "patients": []}

    return {
        "found": True,
        "patients": [
            {"patient_id": p.id, "name": p.name, "phone": p.phone, "gender": p.gender}
            for p in results
        ],
    }
