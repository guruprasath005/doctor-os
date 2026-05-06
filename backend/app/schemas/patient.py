from datetime import date, datetime

from pydantic import BaseModel


class PatientCreate(BaseModel):
    name: str
    phone: str
    dob: date | None = None
    gender: str | None = None


class PatientOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    name: str
    phone: str
    dob: date | None
    gender: str | None
    abha_id: str | None
    allergies: str | None
    consent_given: bool
    created_at: datetime
