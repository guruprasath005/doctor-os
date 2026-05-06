from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_session
from app.schemas.patient import PatientCreate, PatientOut
from app.services.patient import get_patient, register_patient, search_patient

router = APIRouter(prefix="/patients", tags=["patients"])


@router.post("/", response_model=dict)
def create_patient(data: PatientCreate, db: Session = Depends(get_session)):
    return register_patient(db=db, data=data)


@router.get("/{patient_id}", response_model=dict)
def fetch_patient(patient_id: int, db: Session = Depends(get_session)):
    return get_patient(db=db, patient_id=patient_id)


@router.get("/search/{query}", response_model=dict)
def find_patient(query: str, db: Session = Depends(get_session)):
    return search_patient(db=db, query=query)
