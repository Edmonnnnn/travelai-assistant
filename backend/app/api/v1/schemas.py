from pydantic import BaseModel, EmailStr


# --------------------
# Common / system
# --------------------

class PingResponse(BaseModel):
    ping: str


class ErrorResponse(BaseModel):
    error: str
    details: str | None = None


# --------------------
# User schemas
# --------------------

class UserCreate(BaseModel):
    email: EmailStr


class UserOut(BaseModel):
    id: int
    email: EmailStr

    class Config:
        from_attributes = True
