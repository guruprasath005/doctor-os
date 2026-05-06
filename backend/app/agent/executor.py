import json
import logging

from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.schemas.patient import PatientCreate
from app.services import appointment as appointment_service
from app.services import emr as emr_service
from app.services import messenger
from app.services import patient as patient_service
from app.services import prescription as prescription_service

logger = logging.getLogger(__name__)


def _pos_int(args: dict, key: str) -> int | None:
    val = args.get(key)
    if isinstance(val, int) and val > 0:
        return val
    return None


def dispatch(tool_name: str, arguments: str, db: Session, context: dict | None = None) -> dict:
    try:
        args = json.loads(arguments)
    except json.JSONDecodeError:
        logger.error("Could not parse tool arguments for %s: %r", tool_name, arguments)
        return {"error": "Invalid arguments from model"}

    match tool_name:
        # ── Patient ──────────────────────────────────────────────────────────
        case "register_patient":
            try:
                data = PatientCreate(**args)
            except ValidationError as e:
                errors = [f"{err['loc'][0]}: {err['msg']}" for err in e.errors()]
                return {"error": "; ".join(errors)}
            return patient_service.register_patient(db=db, data=data)

        case "get_patient":
            patient_id = _pos_int(args, "patient_id")
            if patient_id is None:
                return {"error": "patient_id must be a positive integer"}
            return patient_service.get_patient(db=db, patient_id=patient_id)

        case "search_patient":
            query = str(args.get("query", "")).strip()
            if len(query) < 2:
                return {"error": "Search query must be at least 2 characters"}
            return patient_service.search_patient(db=db, query=query)

        # ── Appointment ───────────────────────────────────────────────────────
        case "create_appointment":
            patient_id = _pos_int(args, "patient_id")
            doctor_id = _pos_int(args, "doctor_id")
            slot_time = str(args.get("slot_time", "")).strip()
            if patient_id is None:
                return {"error": "patient_id must be a positive integer"}
            if doctor_id is None:
                return {"error": "doctor_id must be a positive integer"}
            if not slot_time:
                return {"error": "slot_time is required (YYYY-MM-DD HH:MM)"}
            return appointment_service.create_appointment(
                db=db, patient_id=patient_id, doctor_id=doctor_id, slot_time=slot_time
            )

        case "get_todays_queue":
            doctor_id = _pos_int(args, "doctor_id")
            if doctor_id is None:
                return {"error": "doctor_id must be a positive integer"}
            return appointment_service.get_todays_queue(db=db, doctor_id=doctor_id)

        case "get_queue_position":
            appointment_id = _pos_int(args, "appointment_id")
            if appointment_id is None:
                return {"error": "appointment_id must be a positive integer"}
            return appointment_service.get_queue_position(db=db, appointment_id=appointment_id)

        case "cancel_appointment":
            appointment_id = _pos_int(args, "appointment_id")
            if appointment_id is None:
                return {"error": "appointment_id must be a positive integer"}
            return appointment_service.cancel_appointment(db=db, appointment_id=appointment_id)

        # ── EMR ───────────────────────────────────────────────────────────────
        case "create_visit":
            patient_id = _pos_int(args, "patient_id")
            if patient_id is None:
                return {"error": "patient_id must be a positive integer"}
            return emr_service.create_visit(db=db, patient_id=patient_id)

        case "structure_emr":
            raw_text = str(args.get("raw_text", "")).strip()
            if len(raw_text) < 10:
                return {"error": "raw_text is too short. Please provide detailed clinical notes."}
            return emr_service.structure_emr(raw_text=raw_text)

        case "save_emr":
            visit_id = _pos_int(args, "visit_id")
            if visit_id is None:
                return {"error": "visit_id must be a positive integer"}
            soap_notes = args.get("soap_notes")
            if not isinstance(soap_notes, dict):
                return {"error": "soap_notes must be an object with subjective, objective, assessment, plan"}
            return emr_service.save_emr(
                db=db,
                visit_id=visit_id,
                soap_notes=soap_notes,
                diagnosis=args.get("diagnosis"),
            )

        # ── Prescription ──────────────────────────────────────────────────────
        case "draft_prescription":
            symptoms = str(args.get("symptoms", "")).strip()
            diagnosis = str(args.get("diagnosis", "")).strip()
            if not symptoms:
                return {"error": "symptoms cannot be empty"}
            if not diagnosis:
                return {"error": "diagnosis cannot be empty"}
            return prescription_service.draft_prescription(symptoms=symptoms, diagnosis=diagnosis)

        case "save_prescription":
            visit_id = _pos_int(args, "visit_id")
            if visit_id is None:
                return {"error": "visit_id must be a positive integer"}
            drugs = args.get("drugs")
            if not isinstance(drugs, list) or len(drugs) == 0:
                return {"error": "drugs must be a non-empty list"}
            return prescription_service.save_prescription(
                db=db,
                visit_id=visit_id,
                drugs=drugs,
                instructions=args.get("instructions"),
            )

        # ── Messaging ─────────────────────────────────────────────────────────
        case "send_message":
            chat_id = str(args.get("chat_id", "")).strip()
            text = str(args.get("text", "")).strip()
            if not chat_id:
                return {"error": "chat_id is required"}
            if not text:
                return {"error": "text cannot be empty"}
            return messenger.send_message(chat_id=chat_id, text=text)

        case "send_reminder":
            appointment_id = _pos_int(args, "appointment_id")
            chat_id = str(args.get("chat_id", "")).strip()
            if appointment_id is None:
                return {"error": "appointment_id must be a positive integer"}
            if not chat_id:
                return {"error": "chat_id is required"}
            appt = appointment_service.get_appointment(db=db, appointment_id=appointment_id)
            if "error" in appt:
                return appt
            text = (
                f"Reminder: Your appointment is confirmed.\n"
                f"Token #{appt['token']} on {appt['slot_time']}\n"
                f"Please arrive 10 minutes early."
            )
            return messenger.send_message(chat_id=chat_id, text=text)

        case _:
            logger.warning("Unknown tool called: %s", tool_name)
            return {"error": f"Unknown tool: {tool_name}"}
