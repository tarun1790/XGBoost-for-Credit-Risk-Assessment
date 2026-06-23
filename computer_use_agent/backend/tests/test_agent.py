import pytest
import asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from uuid import uuid4

# Mock database dependencies before importing orchestrator
import sys
from types import ModuleType

# Create dummy modules or mocks for SQLAlchemy session context to run unit tests without live postgres
mock_session = AsyncMock()

@pytest.fixture
def mock_db():
    return mock_session

@pytest.mark.asyncio
async def test_planner_goal_decomposition():
    """
    Validates that the Executive Planner decomposes high-level text goals
    into structured JSON steps (subtasks) using the fallback engine.
    """
    from app.agents.planner import executive_planner
    
    goal = "Navigate to local borrowers list and extract details"
    plan = await executive_planner.plan_task(goal)
    
    assert isinstance(plan, list)
    assert len(plan) > 0
    assert plan[0]["agent"] == "BROWSER"
    assert plan[0]["action"] == "NAVIGATE"
    assert "url" in plan[0]["details"]

@pytest.mark.asyncio
async def test_validation_agent_rules():
    """
    Validates that the Validation Agent correctly checks DOM status and detects errors.
    """
    from app.agents.validation import validation_agent
    from app.agents.browser_control import browser_agent
    
    # Mock browser DOM inner text with an error keyword
    browser_agent.start = AsyncMock()
    browser_agent.page = MagicMock()
    browser_agent.page.url = "http://localhost:5173/customers"
    browser_agent.get_dom_text = AsyncMock(return_value="Database connection failed! Internal Error.")
    
    failed_step = {
        "agent": "BROWSER",
        "action": "CLICK",
        "details": {"selector": "button.submit"},
        "description": "Click submit"
    }
    
    val_res = await validation_agent.validate_step(failed_step)
    assert val_res["is_valid"] is False
    assert "Error" in val_res["reason"] or "error" in val_res["reason"]

@pytest.mark.asyncio
async def test_self_healing_replanning():
    """
    Validates that the Executive Planner replans and inserts recovery steps upon failure.
    """
    from app.agents.planner import executive_planner
    
    original_plan = [
        {"step": 1, "agent": "BROWSER", "action": "NAVIGATE", "details": {"url": "http://localhost:5173/"}, "description": "Go to site"},
        {"step": 2, "agent": "BROWSER", "action": "CLICK", "details": {"selector": ".btn"}, "description": "Click selector"}
    ]
    
    healed_plan = await executive_planner.replan_on_failure(
        original_plan=original_plan,
        failed_step_index=1,
        error_msg="Selector '.btn' not found on screen"
    )
    
    assert len(healed_plan) == 3
    # Check that a recovery navigation step was injected at index 1
    assert "Recovery" in healed_plan[1]["description"]
    assert healed_plan[1]["action"] == "NAVIGATE"
