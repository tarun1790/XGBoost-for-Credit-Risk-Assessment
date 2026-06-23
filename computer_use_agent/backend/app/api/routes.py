from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from uuid import UUID
from typing import List

from app.core.db import get_db
from app.db.models import Task, Plan, ActionLog, AuditLog
from app.schemas.schemas import TaskCreate, TaskResponse, TaskDetailResponse, ActionLogResponse
from app.agents.orchestrator import execute_task_lifecycle, ACTIVE_WEBSOCKETS

router = APIRouter()

@router.post("/tasks", response_model=TaskResponse)
async def create_task(task_in: TaskCreate, background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """
    Submits a new agent goal and runs the LangGraph state execution loop in the background.
    """
    # Create Task in DB
    task = Task(goal=task_in.goal, status="PENDING")
    db.add(task)
    await db.commit()
    await db.refresh(task)

    # Log audit event
    audit = AuditLog(
        event_type="TASK_CREATED",
        message=f"Created task {task.id} with goal: '{task.goal}'"
    )
    db.add(audit)
    await db.commit()

    # Trigger async background orchestration run
    background_tasks.add_task(execute_task_lifecycle, task.id, task.goal)

    return task

@router.get("/tasks", response_model=List[TaskResponse])
async def list_tasks(db: AsyncSession = Depends(get_db)):
    """
    Retrieves all tasks in the system.
    """
    stmt = select(Task).order_by(Task.created_at.desc())
    res = await db.execute(stmt)
    return res.scalars().all()

@router.get("/tasks/{task_id}", response_model=TaskDetailResponse)
async def get_task_details(task_id: UUID, db: AsyncSession = Depends(get_db)):
    """
    Fetches the comprehensive status of a task including its plan steps and screenshots execution logs.
    """
    stmt = select(Task).where(Task.id == task_id)
    res = await db.execute(stmt)
    task = res.scalar_one_or_none()
    
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    # Fetch Plan
    stmt_plan = select(Plan).where(Plan.task_id == task_id)
    res_plan = await db.execute(stmt_plan)
    task.plan = res_plan.scalar_one_or_none()

    # Fetch Action Logs
    stmt_logs = select(ActionLog).where(ActionLog.task_id == task_id).order_by(ActionLog.executed_at.asc())
    res_logs = await db.execute(stmt_logs)
    task.action_logs = list(res_logs.scalars().all())

    return task

@router.get("/audits", response_model=List[dict])
async def get_audit_logs(db: AsyncSession = Depends(get_db)):
    stmt = select(AuditLog).order_by(AuditLog.created_at.desc()).limit(100)
    res = await db.execute(stmt)
    audits = res.scalars().all()
    return [
        {
            "id": str(a.id),
            "event_type": a.event_type,
            "message": a.message,
            "created_at": a.created_at.isoformat()
        } for a in audits
    ]

@router.websocket("/ws/stream")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket channel for broadcasting real-time agent updates (screenshots, steps) to the dashboard.
    """
    await websocket.accept()
    ACTIVE_WEBSOCKETS.add(websocket)
    try:
        while True:
            # Keep connection alive; ignore any client-sent text
            await websocket.receive_text()
    except WebSocketDisconnect:
        ACTIVE_WEBSOCKETS.remove(websocket)
    except Exception:
        if websocket in ACTIVE_WEBSOCKETS:
            ACTIVE_WEBSOCKETS.remove(websocket)
