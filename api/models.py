import uuid
from enum import Enum
from uuid import UUID

from sqlalchemy import Column, String, DateTime, ForeignKey, Boolean, Enum as SQLAlchemyEnum
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
from sqlalchemy.orm import relationship
from api.database import Base
from api.Categories import Categories
from api.typeOccurence import TypeOccurence
class User(Base):
    __tablename__ = "users"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    username = Column(String, unique=True, index=True)
    email = Column(String, unique=True, index=True)
    password = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime, default=datetime.utcnow)

    events = relationship("Event", back_populates="user")

class Event(Base):
    __tablename__ = "events"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    title = Column(String, unique=True, index=True, nullable=False)
    startDate = Column(DateTime, default=datetime.utcnow, nullable=False)
    endDate = Column(DateTime, default=datetime.utcnow , nullable=False)
    category = Column(SQLAlchemyEnum(Categories), index=True , nullable=True)
    typeOcc = Column(SQLAlchemyEnum(TypeOccurence), index=True , nullable=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    user = relationship("User", back_populates="events")
    reminders = relationship("Reminder", back_populates="event_reminder")
    collaborators = relationship("Collaborateur", back_populates="event")
    pending_invitations = relationship("PendingInvitation", back_populates="event")

class Reminder(Base):
    __tablename__ = 'reminders'
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    reminder_date = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_reminder_sent = Column(Boolean, default=False)

    event_reminder = relationship("Event", back_populates="reminders")

class Collaborateur(Base):
    __tablename__ = "collaborateurs"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, unique=True, index=True)
    event_id = Column(String, ForeignKey("events.id"))
    permission = Column(String, nullable=False)

    event = relationship("Event", back_populates="collaborators")

class PendingInvitation(Base):
    __tablename__ = "pending_invitations"

    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    email = Column(String, index=True, nullable=False)
    event_id = Column(String, ForeignKey("events.id"), nullable=False)
    token = Column(String, unique=True, nullable=False)

    event = relationship("Event", back_populates="pending_invitations")