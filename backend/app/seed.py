# backend/app/seed.py
from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import User


def run_seed(db: Session) -> bool:
    """
    Returns True if seed inserted something, False if skipped.
    Idempotent: does nothing if users already exist.
    """
    # if schema not ready -> will throw ProgrammingError higher up (handled in entrypoint)
    if db.query(User).first():
        return False

    users = [
        User(email="demo@travelai.dev"),
        User(email="admin@travelai.dev"),
    ]

    db.add_all(users)
    db.commit()

    print("▶ Seed: inserted demo users")
    print("▶ Seed finished")
    return True
