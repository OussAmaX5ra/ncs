from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Column, Integer, String, DateTime, Text
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.db.base import Base

if TYPE_CHECKING:
    from .project import Project  # noqa: F401


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean(), default=True)
    is_superuser = Column(Boolean(), default=False)

    # OAuth fields
    google_id = Column(String, unique=True, nullable=True, index=True)


    # Profile fields
    full_name = Column(String, nullable=True)
    avatar_url = Column(Text, nullable=True)
    bio = Column(Text, nullable=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    last_login_at = Column(DateTime(timezone=True), nullable=True)

    files = relationship("File", back_populates="user", cascade="all, delete-orphan")

    roadmaps = relationship("RoadMap", back_populates="user", cascade="all, delete")



