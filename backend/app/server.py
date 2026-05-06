from fastapi import FastAPI

from app.database import init_db
from app.routers import appointment, patient, telegram

app = FastAPI(
    title="Doctor OS API",
    description="Agentic EHR backend — Local Phase",
    version="0.2.0",
)

app.include_router(telegram.router)
app.include_router(patient.router)
app.include_router(appointment.router)


@app.on_event("startup")
def startup():
    init_db()


@app.get("/health")
def health():
    return {"status": "ok"}
