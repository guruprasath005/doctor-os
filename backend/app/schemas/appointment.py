from datetime import datetime

from pydantic import BaseModel


class AppointmentOut(BaseModel):
    model_config = {"from_attributes": True}

    id: int
    patient_id: int
    doctor_id: int
    slot_time: datetime
    token: int
    status: str
    created_at: datetime
