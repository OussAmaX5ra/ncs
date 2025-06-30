import enum
import uuid
from datetime import datetime

from sqlalchemy import String, Column, UUID, Text, Integer, ForeignKey, Float, DateTime
from sqlalchemy import Enum as SqlEnum
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()

class StepState(enum.Enum):
    pending = "pending"
    in_progress = "in-progress"
    completed = "completed"



class RoadMap(Base) :
    __tablename__='roadmap'
    id = Column(Integer, primary_key=True, autoincrement=True)
    Topic = Column(String(100), nullable=False)
    ExpLvl = Column(String(50), nullable=False)
    specificGoals = Column(Text, nullable=True)
    TimeLine = Column(String, nullable=False)

    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    user = relationship("User", back_populates="roadmaps")
    steps = relationship("Step", back_populates="roadmap", cascade="all, delete-orphan")


class Step(Base) :
    __tablename__ = 'step'

    id = Column(Integer, primary_key=True, autoincrement=True)

    state = Column(SqlEnum(StepState, name="step_state"), nullable=False, default=StepState.pending)

    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    estimated_time = Column(String, nullable=True)

    roadmap_id = Column(Integer, ForeignKey("roadmap.id", ondelete="CASCADE"), nullable=False)

    roadmap = relationship("RoadMap", back_populates="steps")

class Noitification(Base) :
    __tablename__ = 'notifications'

    id = Column(Integer, primary_key=True, autoincrement=True)

    text = Column(String(100), nullable=False)

    content = Column(Text, nullable=False)

    submitted_at = Column(DateTime, default=datetime.utcnow)

    event_id = Column(Integer, ForeignKey("events.id", ondelete="CASCADE"), unique=True, nullable=False)
    event = relationship("Event", back_populates="notification")
    notification = relationship("Notification", back_populates="event", uselist=False, cascade="all, delete-orphan")

class File(Base):
    __tablename__ = 'files'

    id = Column(Integer, primary_key=True, autoincrement=True)
    filename = Column(String(255), nullable=False)           # The name of the file
    path = Column(String(500), nullable=False)               # The file system or URL path
    uploaded_at = Column(DateTime, default=datetime.utcnow)  # Timestamp of upload
    # 🔗 Foreign key to User
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # 🔁 Relationship to User
    user = relationship("User", back_populates="files")
