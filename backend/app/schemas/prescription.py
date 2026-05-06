from datetime import datetime

from pydantic import BaseModel, field_validator


class Drug(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: str
    instructions: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Drug name cannot be empty")
        return v[:100]

    @field_validator("dosage")
    @classmethod
    def validate_dosage(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Dosage cannot be empty")
        return v[:50]

    @field_validator("frequency")
    @classmethod
    def validate_frequency(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Frequency cannot be empty")
        return v[:50]

    @field_validator("duration")
    @classmethod
    def validate_duration(cls, v: str) -> str:
        v = v.strip()
        if not v:
            raise ValueError("Duration cannot be empty")
        return v[:50]

    @field_validator("instructions")
    @classmethod
    def validate_instructions(cls, v: str | None) -> str | None:
        if v is None:
            return v
        v = v.strip()
        return v[:200] if v else None


class PrescriptionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    visit_id: int
    drugs: str
    instructions: str | None
    created_at: datetime
