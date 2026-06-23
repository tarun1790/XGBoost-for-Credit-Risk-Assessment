import os
import time
import asyncio
from datetime import datetime
from typing import TypedDict, List, Dict, Any, Optional
from langgraph.graph import StateGraph, END
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.db import SessionLocal
from app.db.models import Task, Plan, ActionLog, AuditLog
from app.core.config import settings
from app.agents.planner import executive_planner
from app.agents.browser_control import browser_agent
from app.agents.desktop_control import desktop_agent
from app.agents.validation import validation_agent
from app.agents.memory import memory_agent

# Global dictionary to track active WebSocket clients for streaming live updates
ACTIVE_WEBSOCKETS = set()

async def broadcast_status(data: dict):
    """
    Utility to broadcast live screenshots/logs to all active dashboard consoles.
    """
    for ws in list(ACTIVE_WEBSOCKETS):
        try:
            await ws.send_json(data)
        except Exception:
            ACTIVE_WEBSOCKETS.remove(ws)

# Define State Structure for LangGraph
class AgentState(TypedDict):
    task_id: str
    goal: str
    plan: List[Dict[str, Any]]
    current_step_index: int
    is_complete: bool
    errors: List[str]
    last_screenshot: Optional[str]

# ----------------- GRAPH NODES -----------------

async def planner_node(state: AgentState) -> AgentState:
    """
    Generates the initial plan if it doesn't exist.
    """
    task_id = state["task_id"]
    goal = state["goal"]
    
    # Check if a plan is already initialized in state
    if not state["plan"]:
        # Query semantic memory to see if we have experienced similar tasks before
        past_experiences = memory_agent.find_similar_experience(goal)
        context_notes = ""
        if past_experiences:
            context_notes = f"Here are similar successful sequences from memory: {past_experiences}"
            
        print(f"Planning goal: {goal}")
        plan_steps = await executive_planner.plan_task(goal, context_notes)
        state["plan"] = plan_steps
        state["current_step_index"] = 0
        
        # Save Plan to Database
        async with SessionLocal() as db:
            db_plan = Plan(task_id=state["task_id"], step_tree=plan_steps, current_step=0)
            db.add(db_plan)
            await db.commit()
            
        await broadcast_status({
            "task_id": str(task_id),
            "event": "PLAN_GENERATED",
            "plan": plan_steps,
            "message": "Executive plan generated successfully."
        })
        
    return state

async def executor_node(state: AgentState) -> AgentState:
    """
    Executes the current plan step using either browser or desktop controllers.
    """
    plan = state["plan"]
    idx = state["current_step_index"]
    task_id = state["task_id"]
    
    if idx >= len(plan):
        state["is_complete"] = True
        return state

    current_step = plan[idx]
    agent_type = current_step.get("agent")
    action = current_step.get("action")
    details = current_step.get("details", {})
    description = current_step.get("description", "")
    
    print(f"Executing step {idx+1}/{len(plan)}: [{agent_type}] {action} - {description}")
    await broadcast_status({
        "task_id": str(task_id),
        "event": "EXECUTING_STEP",
        "current_step": idx,
        "step_details": current_step
    })
    
    result = {"success": False, "error": "Unknown execution context"}
    screenshot_name = f"step_{task_id}_{idx+1}_{int(time.time() if 'time' in globals() else 100)}.png"
    screenshot_path = ""

    # Execute BROWSER operations
    if agent_type == "BROWSER":
        if action == "NAVIGATE":
            result = await browser_agent.navigate(details.get("url"))
        elif action == "CLICK":
            result = await browser_agent.click(details.get("selector"), details.get("text_match"))
        elif action == "FILL":
            result = await browser_agent.fill(details.get("selector"), details.get("value"))
        elif action == "UPLOAD":
            result = await browser_agent.upload_file(details.get("selector"), details.get("filepath"))
        elif action == "SCRAPE":
            text = await browser_agent.get_dom_text()
            result = {"success": True, "scraped_length": len(text), "data_preview": text[:200]}
            
        # Capture screenshot for visual audit
        screenshot_path = await browser_agent.capture_screenshot(screenshot_name)

    # Execute DESKTOP operations
    elif agent_type == "DESKTOP":
        if action == "CLICK":
            result = desktop_agent.click(details.get("x", 0), details.get("y", 0))
        elif action == "TYPE":
            result = desktop_agent.type(details.get("text", ""), details.get("press_enter", False))
        elif action == "HOTKEY":
            result = desktop_agent.press_key(details.get("key_combination", ""))
            
        # Capture physical desktop screenshot
        screenshot_path = desktop_agent.capture_desktop_screenshot(screenshot_name)

    # Convert absolute screenshot path to a relative static web path for react frontends
    web_screenshot_path = f"/static/screenshots/{os.path.basename(screenshot_path)}" if screenshot_path else ""
    state["last_screenshot"] = web_screenshot_path

    # Save execution outcome to action logs database
    is_success = result.get("success", True)
    error_msg = result.get("error") if not is_success else None
    
    async with SessionLocal() as db:
        action_log = ActionLog(
            task_id=state["task_id"],
            step_name=description,
            agent_type=agent_type,
            action_type=action,
            action_details=details,
            screenshot_path=web_screenshot_path,
            is_success=is_success,
            error_message=error_msg
        )
        db.add(action_log)
        await db.commit()

    if not is_success:
        state["errors"].append(error_msg or "Action execution failed")
        
    await broadcast_status({
        "task_id": str(task_id),
        "event": "STEP_COMPLETED",
        "current_step": idx,
        "is_success": is_success,
        "screenshot": web_screenshot_path,
        "error": error_msg
    })
    
    return state

async def validator_node(state: AgentState) -> AgentState:
    """
    Verifies step outcomes. If a failure is detected, triggers healing recovery.
    """
    plan = state["plan"]
    idx = state["current_step_index"]
    
    # If the step already encountered an execution error
    if state["errors"]:
        return state

    current_step = plan[idx]
    
    # Run validation checks on DOM/Screenshots
    val_result = await validation_agent.validate_step(current_step)
    if not val_result["is_valid"]:
        state["errors"].append(val_result["reason"])
        
    return state

async def recovery_node(state: AgentState) -> AgentState:
    """
    Self-healing replanning node triggered when errors are raised in state.
    """
    if not state["errors"]:
        return state

    task_id = state["task_id"]
    error_msg = state["errors"][-1]
    idx = state["current_step_index"]
    plan = state["plan"]
    
    print(f"Self-Healing Agent: Recovering from error: {error_msg}")
    await broadcast_status({
        "task_id": str(task_id),
        "event": "HEALING_RECOVERY",
        "current_step": idx,
        "error": error_msg,
        "message": "Self-healing triggered. Re-planning remaining steps."
    })
    
    # Call planner to adjust the plan steps dynamically
    healed_plan = await executive_planner.replan_on_failure(plan, idx, error_msg)
    state["plan"] = healed_plan
    state["errors"] = [] # Clear active error to resume execution loop
    
    # Update plan database
    async with SessionLocal() as db:
        stmt = select(Plan).where(Plan.task_id == task_id)
        res = await db.execute(stmt)
        db_plan = res.scalar_one_or_none()
        if db_plan:
            db_plan.step_tree = healed_plan
            await db.commit()

    return state

async def memory_sync_node(state: AgentState) -> AgentState:
    """
    Stores logs, increments step index, and loops.
    """
    # If we had errors and didn't recover, do not advance
    if state["errors"]:
        return state
        
    state["current_step_index"] += 1
    
    # Update plan current index in db
    async with SessionLocal() as db:
        stmt = select(Plan).where(Plan.task_id == state["task_id"])
        res = await db.execute(stmt)
        db_plan = res.scalar_one_or_none()
        if db_plan:
            db_plan.current_step = state["current_step_index"]
            await db.commit()
            
    return state

# ----------------- DECISION ROUTER -----------------

def route_next(state: AgentState):
    """
    Determines next state graph transitions based on current outcome status.
    """
    if state["is_complete"] or state["current_step_index"] >= len(state["plan"]):
        return "end"
    if state["errors"]:
        return "recovery"
    return "memory_sync"

# ----------------- BUILD GRAPH -----------------

workflow = StateGraph(AgentState)

# Add Nodes
workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("validator", validator_node)
workflow.add_node("recovery", recovery_node)
workflow.add_node("memory_sync", memory_sync_node)

# Set Entry Point
workflow.set_entry_point("planner")

# Add Links
workflow.add_edge("planner", "executor")
workflow.add_edge("executor", "validator")

# Conditional routing from validation
workflow.add_conditional_edges(
    "validator",
    route_next,
    {
        "end": END,
        "recovery": "recovery",
        "memory_sync": "memory_sync"
    }
)

workflow.add_edge("recovery", "executor") # return to executor once re-planned
workflow.add_edge("memory_sync", "planner") # loop back to planner

agent_executor = workflow.compile()

# ----------------- EXECUTIVE MANAGER -----------------

async def execute_task_lifecycle(task_id: str, goal: str):
    """
    Starts the full LangGraph state execution loop for a submitted goal.
    """
    # Initialize state
    initial_state: AgentState = {
        "task_id": task_id,
        "goal": goal,
        "plan": [],
        "current_step_index": 0,
        "is_complete": False,
        "errors": [],
        "last_screenshot": None
    }
    
    # Update task status to EXECUTING
    async with SessionLocal() as db:
        stmt = select(Task).where(Task.id == task_id)
        res = await db.execute(stmt)
        db_task = res.scalar_one_or_none()
        if db_task:
            db_task.status = "EXECUTING"
            await db.commit()

    # Run LangGraph Engine
    try:
        final_state = await agent_executor.ainvoke(initial_state)
        is_success = final_state["is_complete"] and not final_state["errors"]
        
        status = "SUCCESS" if is_success else "FAILED"
        print(f"Goal complete: {status}")
        
        # Save outcome to memory layer for continual learning
        memory_agent.add_episodic_memory(goal, final_state["plan"], is_success)
        
        # Log event in audits
        async with SessionLocal() as db:
            audit = AuditLog(
                event_type="TASK_FINISHED",
                message=f"Task {task_id} execution finished with status {status}",
                metadata_json={"goal": goal, "is_success": is_success}
            )
            db.add(audit)
            
            # Update task table
            stmt = select(Task).where(Task.id == task_id)
            res = await db.execute(stmt)
            db_task = res.scalar_one_or_none()
            if db_task:
                db_task.status = status
                db_task.completed_at = datetime.utcnow()
            await db.commit()
            
        await broadcast_status({
            "task_id": str(task_id),
            "event": "TASK_FINISHED",
            "status": status,
            "message": f"Task execution finished: {status}."
        })
    except Exception as e:
        # Unexpected crash
        print(f"Graph execution crashed: {e}")
        async with SessionLocal() as db:
            stmt = select(Task).where(Task.id == task_id)
            res = await db.execute(stmt)
            db_task = res.scalar_one_or_none()
            if db_task:
                db_task.status = "FAILED"
                db_task.completed_at = datetime.utcnow()
            await db.commit()
            
        await broadcast_status({
            "task_id": str(task_id),
            "event": "TASK_FINISHED",
            "status": "FAILED",
            "message": f"Execution crashed: {str(e)}"
        })
    finally:
        # Shut down browser session gracefully
        await browser_agent.stop()
