from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.services.appointment import (
    cancel_appointment,
    create_appointment,
    get_todays_queue,
)

router = APIRouter(prefix="/appointments", tags=["appointments"])


@router.post("/", response_model=dict)
def book_appointment(
    patient_id: int,
    doctor_id: int,
    slot_time: str,
    db: Session = Depends(get_session),
):
    return create_appointment(db=db, patient_id=patient_id, doctor_id=doctor_id, slot_time=slot_time)


@router.get("/queue/{doctor_id}", response_model=dict)
def todays_queue(doctor_id: int, db: Session = Depends(get_session)):
    return get_todays_queue(db=db, doctor_id=doctor_id)


@router.delete("/{appointment_id}", response_model=dict)
def cancel(appointment_id: int, db: Session = Depends(get_session)):
    return cancel_appointment(db=db, appointment_id=appointment_id)
