from sqlalchemy import Column, DateTime, Integer, String

from app.database import Base, now


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    role = Column(String, default="user", nullable=False)
    name = Column(String, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    token_version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)
    deleted_at = Column(DateTime, nullable=True)
