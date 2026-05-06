import json

from sqlalchemy.orm import Session

from app.schemas.patient import PatientCreate
from app.services import appointment as appointment_service
from app.services import emr as emr_service
from app.services import messenger
from app.services import patient as patient_service
from app.services import prescription as prescription_service


def dispatch(tool_name: str, arguments: str, db: Session, context: dict | None = None) -> dict:
    args = json.loads(arguments)
    ctx = context or {}

    match tool_name:
        # ── Patient ──────────────────────────────────────────────────────────
        case "register_patient":
            return patient_service.register_patient(db=db, data=PatientCreate(**args))

        case "get_patient":
            return patient_service.get_patient(db=db, patient_id=args["patient_id"])

        case "search_patient":
            return patient_service.search_patient(db=db, query=args["query"])

        # ── Appointment ───────────────────────────────────────────────────────
        case "create_appointment":
            return appointment_service.create_appointment(
                db=db,
                patient_id=args["patient_id"],
                doctor_id=args["doctor_id"],
                slot_time=args["slot_time"],
            )

        case "get_todays_queue":
            return appointment_service.get_todays_queue(db=db, doctor_id=args["doctor_id"])

        case "get_queue_position":
            return appointment_service.get_queue_position(db=db, appointment_id=args["appointment_id"])

        case "cancel_appointment":
            return appointment_service.cancel_appointment(db=db, appointment_id=args["appointment_id"])

        # ── EMR ───────────────────────────────────────────────────────────────
        case "create_visit":
            return emr_service.create_visit(db=db, patient_id=args["patient_id"])

        case "structure_emr":
            return emr_service.structure_emr(raw_text=args["raw_text"])

        case "save_emr":
            return emr_service.save_emr(
                db=db,
                visit_id=args["visit_id"],
                soap_notes=args["soap_notes"],
                diagnosis=args.get("diagnosis"),
            )

        # ── Prescription ──────────────────────────────────────────────────────
        case "draft_prescription":
            return prescription_service.draft_prescription(
                symptoms=args["symptoms"],
                diagnosis=args["diagnosis"],
            )

        case "save_prescription":
            return prescription_service.save_prescription(
                db=db,
                visit_id=args["visit_id"],
                drugs=args["drugs"],
                instructions=args.get("instructions"),
            )

        # ── Messaging ─────────────────────────────────────────────────────────
        case "send_message":
            return messenger.send_message(chat_id=args["chat_id"], text=args["text"])

        case "send_reminder":
            appt = appointment_service.get_appointment(db=db, appointment_id=args["appointment_id"])
            if "error" in appt:
                return appt
            text = (
                f"Reminder: Your appointment at the clinic is confirmed.\n"
                f"Token #{appt['token']} — {appt['slot_time']}\n"
                f"Please arrive 10 minutes early."
            )
            return messenger.send_message(chat_id=args["chat_id"], text=text)

        case _:
            return {"error": f"Unknown tool: {tool_name}"}
