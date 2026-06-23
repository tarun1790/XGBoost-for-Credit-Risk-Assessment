import json
import httpx
from app.core.config import settings

class ExecutivePlanner:
    def __init__(self):
        self.ollama_url = f"{settings.OLLAMA_BASE_URL}/api/generate"
        self.model_name = settings.OLLAMA_MODEL

    async def plan_task(self, goal: str, context_notes: str = "") -> list:
        """
        Decomposes a high-level goal into an ordered sequence of executable subtasks.
        """
        prompt = f"""
        You are the Executive Planner for an Autonomous Computer Use Agent.
        Decompose this goal into a list of executable action step JSON blocks.
        
        GOAL: "{goal}"
        CONTEXT: {context_notes}
        
        Available Agents & Actions:
        1. BROWSER: NAVIGATE (url), CLICK (selector, text_match), FILL (selector, value), UPLOAD (selector, filepath), SCRAPE
        2. DESKTOP: CLICK (x, y), TYPE (text, press_enter), HOTKEY (keys)
        
        Format output strictly as a JSON array of step dictionaries:
        [
          {{"step": 1, "agent": "BROWSER", "action": "NAVIGATE", "details": {{"url": "https://example.com"}}, "description": "Go to example"}},
          {{"step": 2, "agent": "BROWSER", "action": "CLICK", "details": {{"selector": "button.submit", "text_match": "Submit"}}, "description": "Click submit"}}
        ]
        """
        
        try:
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.post(
                    self.ollama_url,
                    json={
                        "model": self.model_name,
                        "prompt": prompt,
                        "stream": False,
                        "format": "json"
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    plan_data = json.loads(result.get("response", "[]"))
                    if isinstance(plan_data, list) and len(plan_data) > 0:
                        return plan_data
        except Exception as e:
            print(f"Ollama Planner failed: {e}. Using deterministic plan rule fallback.")
            
        # Deterministic rule-based fallback planner for testing
        return self._generate_fallback_plan(goal)

    def _generate_fallback_plan(self, goal: str) -> list:
        goal_lower = goal.lower()
        if "dashboard" in goal_lower or "borrower" in goal_lower:
            return [
                {
                    "step": 1,
                    "agent": "BROWSER",
                    "action": "NAVIGATE",
                    "details": {"url": "http://localhost:5173/"},
                    "description": "Navigate to local credit risk dashboard"
                },
                {
                    "step": 2,
                    "agent": "BROWSER",
                    "action": "CLICK",
                    "details": {"selector": "button", "text_match": "Scroll to Dashboard"},
                    "description": "Scroll down to show main dashboard metrics"
                },
                {
                    "step": 3,
                    "agent": "BROWSER",
                    "action": "CLICK",
                    "details": {"selector": "a[href='/customers']", "text_match": "Borrowers"},
                    "description": "Click Borrowers directory link in sidebar"
                },
                {
                    "step": 4,
                    "agent": "BROWSER",
                    "action": "SCRAPE",
                    "details": {},
                    "description": "Extract text data from the borrowers directory table"
                }
            ]
        else:
            # Default generic backup plan
            return [
                {
                    "step": 1,
                    "agent": "BROWSER",
                    "action": "NAVIGATE",
                    "details": {"url": "https://google.com"},
                    "description": "Navigate to Google"
                },
                {
                    "step": 2,
                    "agent": "BROWSER",
                    "action": "FILL",
                    "details": {"selector": "input[name='q']", "value": goal},
                    "description": "Enter the goal query in the search input box"
                },
                {
                    "step": 3,
                    "agent": "BROWSER",
                    "action": "CLICK",
                    "details": {"selector": "input[type='submit']", "text_match": "Google Search"},
                    "description": "Click search submit button"
                }
            ]

    async def replan_on_failure(self, original_plan: list, failed_step_index: int, error_msg: str) -> list:
        """
        Re-plans the remaining steps in the plan starting from the failed step.
        """
        print(f"Replanning triggered at step {failed_step_index} due to: {error_msg}")
        # Insert a recovery navigation/click step to reset state and keep the rest
        recovery_step = {
            "step": failed_step_index + 1,
            "agent": "BROWSER",
            "action": "NAVIGATE",
            "details": {"url": "http://localhost:5173/"},
            "description": f"Recovery: Return to root dashboard to reset layout"
        }
        
        new_plan = original_plan[:failed_step_index]
        new_plan.append(recovery_step)
        
        # Shift step indices of remaining tasks
        for idx, step in enumerate(original_plan[failed_step_index:]):
            step["step"] = failed_step_index + 2 + idx
            new_plan.append(step)
            
        return new_plan

executive_planner = ExecutivePlanner()
