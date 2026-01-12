from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from app.api.v1.schemas import PingResponse, UserCreate, UserOut, ErrorResponse
from app.db import get_db
from app.models import User

router = APIRouter(prefix="/api/v1")

@router.get("/ping", response_model=PingResponse)
def ping():
    return PingResponse(ping="ok")

@router.post(
    "/users",
    response_model=UserOut,
    responses={
        409: {"model": ErrorResponse},
    },
)
def create_user(payload: UserCreate, db: Session = Depends(get_db)):
    user = User(email=payload.email)
    db.add(user)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=ErrorResponse(
                error="email_exists",
                details="User with this email already exists",
            ).dict(),
        )
    db.refresh(user)
    return user

@router.get("/users", response_model=list[UserOut])
def list_users(db: Session = Depends(get_db)):
    return db.query(User).all()
