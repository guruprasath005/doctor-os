from datetime import datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models.appointment import Appointment
from app.models.doctor import Doctor
from app.models.patient import Patient


def create_appointment(db: Session, patient_id: int, doctor_id: int, slot_time: str) -> dict:
    patient = db.query(Patient).filter(Patient.id == patient_id).first()
    if not patient:
        return {"error": f"Patient {patient_id} not found"}

    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return {"error": f"Doctor {doctor_id} not found"}

    try:
        slot_dt = datetime.strptime(slot_time, "%Y-%m-%d %H:%M")
    except ValueError:
        return {"error": "Invalid slot_time format. Use YYYY-MM-DD HH:MM"}

    if slot_dt <= datetime.now():
        return {"error": "Cannot book an appointment in the past"}

    slot_date = slot_dt.date()

    existing = (
        db.query(Appointment)
        .filter(
            Appointment.patient_id == patient_id,
            Appointment.doctor_id == doctor_id,
            func.date(Appointment.slot_time) == slot_date,
            Appointment.status != "cancelled",
        )
        .first()
    )
    if existing:
        return {
            "already_booked": True,
            "appointment_id": existing.id,
            "token": existing.token,
            "slot_time": existing.slot_time.strftime("%Y-%m-%d %H:%M"),
            "message": f"{patient.name} already has Token #{existing.token} on {slot_date}. No new booking needed.",
        }

    token = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.doctor_id == doctor_id,
            func.date(Appointment.slot_time) == slot_date,
            Appointment.status != "cancelled",
        )
        .scalar()
        or 0
    ) + 1

    appointment = Appointment(
        patient_id=patient_id,
        doctor_id=doctor_id,
        slot_time=slot_dt,
        token=token,
        status="confirmed",
    )
    db.add(appointment)
    db.commit()
    db.refresh(appointment)

    return {
        "success": True,
        "appointment_id": appointment.id,
        "patient_name": patient.name,
        "doctor_name": doctor.name,
        "slot_time": slot_dt.strftime("%Y-%m-%d %H:%M"),
        "token": token,
        "status": "confirmed",
    }


def get_todays_queue(db: Session, doctor_id: int) -> dict:
    doctor = db.query(Doctor).filter(Doctor.id == doctor_id).first()
    if not doctor:
        return {"error": f"Doctor {doctor_id} not found"}

    today = datetime.now().date()
    appointments = (
        db.query(Appointment)
        .filter(
            Appointment.doctor_id == doctor_id,
            func.date(Appointment.slot_time) == today,
            Appointment.status != "cancelled",
        )
        .order_by(Appointment.token)
        .all()
    )

    queue = []
    for appt in appointments:
        patient = db.query(Patient).filter(Patient.id == appt.patient_id).first()
        queue.append(
            {
                "token": appt.token,
                "appointment_id": appt.id,
                "patient_name": patient.name if patient else "Unknown",
                "patient_phone": patient.phone if patient else "",
                "slot_time": appt.slot_time.strftime("%H:%M"),
                "status": appt.status,
            }
        )

    return {
        "success": True,
        "date": str(today),
        "doctor_name": doctor.name,
        "total": len(queue),
        "queue": queue,
    }


def get_queue_position(db: Session, appointment_id: int) -> dict:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        return {"error": f"Appointment {appointment_id} not found"}

    if appointment.status == "cancelled":
        return {"error": "This appointment has been cancelled"}

    ahead = (
        db.query(func.count(Appointment.id))
        .filter(
            Appointment.doctor_id == appointment.doctor_id,
            func.date(Appointment.slot_time) == appointment.slot_time.date(),
            Appointment.token < appointment.token,
            Appointment.status == "confirmed",
        )
        .scalar()
        or 0
    )

    return {
        "success": True,
        "appointment_id": appointment_id,
        "token": appointment.token,
        "patients_ahead": ahead,
        "estimated_wait_minutes": ahead * 10,
        "status": appointment.status,
    }


def cancel_appointment(db: Session, appointment_id: int) -> dict:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        return {"error": f"Appointment {appointment_id} not found"}

    if appointment.status == "cancelled":
        return {"error": "Appointment is already cancelled"}

    appointment.status = "cancelled"
    db.commit()

    return {"success": True, "appointment_id": appointment_id, "status": "cancelled"}


def get_appointment(db: Session, appointment_id: int) -> dict:
    appointment = db.query(Appointment).filter(Appointment.id == appointment_id).first()
    if not appointment:
        return {"error": f"Appointment {appointment_id} not found"}

    patient = db.query(Patient).filter(Patient.id == appointment.patient_id).first()

    return {
        "appointment_id": appointment.id,
        "patient_id": appointment.patient_id,
        "patient_name": patient.name if patient else "Unknown",
        "patient_phone": patient.phone if patient else "",
        "slot_time": appointment.slot_time.strftime("%Y-%m-%d %H:%M"),
        "token": appointment.token,
        "status": appointment.status,
    }
