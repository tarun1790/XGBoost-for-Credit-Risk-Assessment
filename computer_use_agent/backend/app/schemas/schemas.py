from pydantic import BaseModel, Field
from uuid import UUID
from datetime import datetime
from typing import List, Optional, Dict, Any

class TaskCreate(BaseModel):
    goal: str = Field(..., description="High-level text goal for the agent to execute")

class ActionLogResponse(BaseModel):
    id: UUID
    step_name: str
    agent_type: str
    action_type: str
    action_details: Optional[Dict[str, Any]] = None
    screenshot_path: Optional[str] = None
    is_success: bool
    error_message: Optional[str] = None
    executed_at: datetime

    class Config:
        from_attributes = True

class PlanResponse(BaseModel):
    step_tree: List[Dict[str, Any]]
    current_step: int
    updated_at: datetime

    class Config:
        from_attributes = True

class TaskResponse(BaseModel):
    id: UUID
    goal: str
    status: str
    created_at: datetime
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True

class TaskDetailResponse(TaskResponse):
    plan: Optional[PlanResponse] = None
    action_logs: List[ActionLogResponse] = []

    class Config:
        from_attributes = True

class HITLApproval(BaseModel):
    task_id: UUID
    action_id: str
    approved: bool
    feedback: Optional[str] = None
