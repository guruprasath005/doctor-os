from datetime import datetime

from pydantic import BaseModel


class SOAPNotes(BaseModel):
    subjective: str
    objective: str
    assessment: str
    plan: str


class VisitOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    patient_id: int
    chief_complaint: str | None
    soap_notes: str | None
    diagnosis: str | None
    closed_at: datetime | None
    created_at: datetime
