from datetime import date, datetime

from pydantic import BaseModel, field_validator


class PatientCreate(BaseModel):
    name: str
    phone: str
    dob: date | None = None
    gender: str | None = None
    consent_given: bool = True

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Patient name cannot be empty")
        if v.replace(" ", "").isdigit():
            raise ValueError("Patient name cannot be numeric")
        return v

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        v = v.strip().replace(" ", "").replace("-", "")
        if v.startswith("+91"):
            v = v[3:]
        if v.startswith("91") and len(v) == 12:
            v = v[2:]
        if not v.isdigit() or len(v) != 10:
            raise ValueError("Phone must be a valid 10-digit Indian mobile number")
        return v

    @field_validator("gender")
    @classmethod
    def validate_gender(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip().lower()
        if v not in {"male", "female", "other"}:
            raise ValueError("Gender must be male, female, or other")
        return v

    @field_validator("dob")
    @classmethod
    def validate_dob(cls, v: date | None) -> date | None:
        if v is None:
            return v
        if v >= date.today():
            raise ValueError("Date of birth must be in the past")
        return v


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
