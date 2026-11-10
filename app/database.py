from collections.abc import Generator
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.config import ROOT, settings


def build_url() -> str:
    url = make_url(settings.database_url)
    if settings.read_only and url.get_backend_name() == "sqlite" and url.database:
        path = Path(url.database)
        if not path.is_absolute():
            path = ROOT / path
        return f"sqlite:///file:{path.as_posix()}?mode=ro&uri=true"
    return settings.database_url


DATABASE_URL = build_url()

# check_same_thread só é necessário (e só existe) no SQLite
connect_args = (
    {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
)

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
