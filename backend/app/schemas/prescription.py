from datetime import datetime

from pydantic import BaseModel


class Drug(BaseModel):
    name: str
    dosage: str
    frequency: str
    duration: str
    instructions: str | None = None


class PrescriptionOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    visit_id: int
    drugs: str
    instructions: str | None
    created_at: datetime
