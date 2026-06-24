import uuid
from sqlalchemy import Column, String, DateTime, Boolean, Integer, ForeignKey, JSON, Float
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from datetime import datetime
from app.core.db import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="ANALYST") # ADMIN, ANALYST
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class Task(Base):
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal = Column(String, nullable=False)
    status = Column(String, default="PENDING") # PENDING, EXECUTING, PAUSED, SUCCESS, FAILED
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime, nullable=True)

    executions = relationship("Execution", back_populates="task", cascade="all, delete-orphan")


class Execution(Base):
    __tablename__ = "executions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id", ondelete="CASCADE"))
    current_step = Column(Integer, default=0)
    status = Column(String, default="RUNNING") # RUNNING, PAUSED, SUCCESS, FAILED
    step_tree = Column(JSON, nullable=False) # The plan steps list
    started_at = Column(DateTime, default=datetime.utcnow)
    finished_at = Column(DateTime, nullable=True)

    task = relationship("Task", back_populates="executions")
    logs = relationship("ActionLog", back_populates="execution", cascade="all, delete-orphan")
    screenshots = relationship("Screenshot", back_populates="execution", cascade="all, delete-orphan")


class ActionLog(Base):
    __tablename__ = "logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"))
    step_name = Column(String, nullable=False)
    agent_type = Column(String, nullable=False) # BROWSER, DESKTOP
    action_type = Column(String, nullable=False) # CLICK, TYPE, etc.
    action_details = Column(JSON, nullable=True)
    is_success = Column(Boolean, default=True)
    error_message = Column(String, nullable=True)
    executed_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="logs")


class Screenshot(Base):
    __tablename__ = "screenshots"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    execution_id = Column(UUID(as_uuid=True), ForeignKey("executions.id", ondelete="CASCADE"))
    step_index = Column(Integer, nullable=False)
    file_path = Column(String, nullable=False) # Saved in C:\AgentEvidence
    bounding_boxes = Column(JSON, nullable=True) # Visually detected elements
    created_at = Column(DateTime, default=datetime.utcnow)

    execution = relationship("Execution", back_populates="screenshots")


class Memory(Base):
    __tablename__ = "memory"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    key = Column(String, unique=True, nullable=False)
    val = Column(JSON, nullable=False)
    metadata_json = Column(JSON, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class Workflow(Base):
    __tablename__ = "workflows"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String, unique=True, nullable=False)
    step_tree = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
