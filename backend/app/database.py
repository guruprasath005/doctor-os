from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import settings

engine = create_engine(
    f"sqlite:///{settings.db_path}",
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


class Base(DeclarativeBase):
    pass


def get_session():
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def init_db():
    import app.models  # noqa: F401 — registers all models with Base metadata
    Base.metadata.create_all(bind=engine)
    _seed_default_doctor()


def _seed_default_doctor():
    from app.models.doctor import Doctor

    db = SessionLocal()
    try:
        if not db.query(Doctor).first():
            db.add(Doctor(name="Dr. Default", reg_number="MCI-00001", speciality="General Practice"))
            db.commit()
    finally:
        db.close()
