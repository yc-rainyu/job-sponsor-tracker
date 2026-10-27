from collections.abc import Generator

from sqlalchemy.orm import Session

from app.db.engine import SessionLocal


def get_db() -> Generator[Session]:
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()
