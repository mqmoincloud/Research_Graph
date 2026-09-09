"""Passwords and tokens - the same chain CaseDesk uses.

    verify_token       is this a real, unexpired token?
    get_current_user   does it still point at a live user?
    require_admin      and is that user an admin?

Each one depends on the one above it, so a route only has to ask for the level
it needs and the checks below it happen on their own.
"""

from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.config import config
from app.database import get_db
from app.models import User

pwd_context = CryptContext(schemes=["bcrypt"])


def hash_password(password: str):
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str):
    return pwd_context.verify(plain_password, hashed_password)


def create_token(data: dict):
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + timedelta(minutes=config.token_minutes)
    to_encode.update({"exp": expire})

    token = jwt.encode(to_encode, config.secret_key, algorithm=config.algorithm)

    return token

bearer_scheme = HTTPBearer(auto_error=False)


def verify_token(credentials: HTTPAuthorizationCredentials = Depends(bearer_scheme)):

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated"
        )

    try:
        # .credentials is the part after "Bearer ".
        payload = jwt.decode(
            credentials.credentials, config.secret_key, algorithms=[config.algorithm]
        )
        return payload

    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )


def get_current_user(user_data: dict = Depends(verify_token), db: Session = Depends(get_db)):
    
    current_user = db.query(User).filter(
        User.id == user_data.get("sub"),
        User.deleted_at.is_(None),
    ).first()

    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="User is Not verified"
        )

    # Password changed since this token was handed out, so it is stale.
    if user_data.get("ver") != current_user.token_version:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )

    return current_user


def require_admin(current_user: User = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(
            status_code=403,
            detail="Admins Only"
        )
    return current_user
