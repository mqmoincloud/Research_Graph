from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class UserSignup(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    # 72 is bcrypt's own limit - it silently ignores anything past byte 72,
    # so a longer password would appear to work and then not matter.
    password: str = Field(min_length=8, max_length=72)

    # No role field on purpose. If it were here, anyone could sign up as an
    # admin just by adding one line to the request body.


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str


class UserUpdate(BaseModel):
    """What an admin may change about someone else."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    email: EmailStr | None = None
    password: str | None = Field(default=None, min_length=8, max_length=72)
    role: Literal["admin", "user"] | None = None

    # All three columns are NOT NULL, so an explicit null would reach the
    # database and come back as a 500. Leaving a field out is still fine - a
    # default is never validated.
    @field_validator("name", "email", "role")
    @classmethod
    def cannot_be_null(cls, value):
        if value is None:
            raise ValueError("cannot be null")
        return value


class ProfileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    email: EmailStr
    role: str
    created_at: datetime


class ProfileUpdate(BaseModel):
    # Email is deliberately not here. It is the login identifier, and changing
    # it by mistake locks you out - an admin can do it if it is really needed.
    name: str = Field(min_length=1, max_length=100)


class PasswordChange(BaseModel):
    current_password: str
    new_password: str = Field(min_length=8, max_length=72)
