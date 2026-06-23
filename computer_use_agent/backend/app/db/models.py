import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base

class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, EXECUTING, SUCCESS, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    plan = relationship("Plan", back_populates="task", uselist=False, cascade="all, delete-orphan")
    action_logs = relationship("ActionLog", back_populates="task", cascade="all, delete-orphan")


class Plan(Base):
    __tablename__ = "plans"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"), unique=True)
    step_tree = Column(JSON, nullable=False) # List of subtasks/steps
    current_step = Column(Integer, default=0)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    task = relationship("Task", back_populates="plan")


class ActionLog(Base):
    __tablename__ = "action_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    step_name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False) # BROWSER, DESKTOP
    action_type = Column(String, nullable=False) # CLICK, TYPE, NAVIGATE, UPLOAD, DOWNLOAD, SCRAPE
    action_details = Column(JSON, nullable=True) # Input value, coordinates, tag name, etc.
    screenshot_path = Column(String, nullable=True)
    is_success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    task = relationship("Task", back_populates="action_logs")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    event_type = Column(String, nullable=False)
    message = Column(String, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
