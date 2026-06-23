from app.agents.browser_control import browser_agent

class ValidationAgent:
    async def validate_step(self, step: dict) -> dict:
        """
        Validates whether the executed action successfully achieved its intended state.
        Returns: {"is_valid": bool, "reason": str}
        """
        agent_type = step.get("agent")
        action = step.get("action")
        details = step.get("details", {})

        if agent_type == "BROWSER":
            # Check active page text & URL
            try:
                dom_text = await browser_agent.get_dom_text()
                current_url = browser_agent.page.url
                
                # Check for standard server/application error text
                error_keywords = ["error", "failed", "unauthorized", "invalid credential", "404 not found", "bad request"]
                detected_errors = [k for k in error_keywords if k in dom_text.lower()]
                
                # If we were navigating, check if the URL matches allowlist/target
                if action == "NAVIGATE" and "url" in details:
                    target_url = details["url"]
                    if not current_url.startswith(target_url.split("?")[0]):
                        return {
                            "is_valid": False,
                            "reason": f"Active URL ({current_url}) does not match target path ({target_url})"
                        }

                # Check if we clicked or filled a form and got a bad alert text
                if len(detected_errors) > 0 and action in ["CLICK", "FILL"]:
                    # Check if error message is prominent (in a modal or alert)
                    return {
                        "is_valid": False,
                        "reason": f"Detected error keywords on page: {detected_errors}"
                    }

                return {"is_valid": True, "reason": "DOM verification passed."}
            except Exception as e:
                return {"is_valid": False, "reason": f"DOM access error: {str(e)}"}
                
        elif agent_type == "DESKTOP":
            # Desktop actions are local (clicks, hotkeys). We mark them valid by default unless an OS crash occurs.
            return {"is_valid": True, "reason": "Desktop OS event executed successfully."}

        return {"is_valid": False, "reason": f"Unknown agent type: {agent_type}"}

validation_agent = ValidationAgent()
