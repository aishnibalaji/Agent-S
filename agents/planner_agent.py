"""
planner agent: breaks down high-level test goals into specific, actionable steps
"""
from typing import List, Dict, Any
import json
from .base_agent import BaseAgent, AgentMessage

class PlannerAgent(BaseAgent):
    
    def __init__(self, llm_client):
        super().__init__("PlannerAgent", llm_client)
        
    def process(self, message: AgentMessage) -> AgentMessage:
        if message.message_type == "create_plan":
            plan = self._create_test_plan(message.content["goal"])
            return self.send_message(
                recipient="ExecutorAgent",
                message_type="execute_plan",
                content={"plan": plan}
            )
        elif message.message_type == "replan_needed":
            # Handle dynamic replanning; error handling
            new_plan = self._adapt_plan(
                original_goal=message.content["original_goal"],
                current_state=message.content["current_state"],
                error=message.content["error"]
            )
            return self.send_message(
                recipient="ExecutorAgent",
                message_type="execute_plan",
                content={"plan": new_plan, "is_recovery": True}
            )
            
    def _create_test_plan(self, goal: str) -> List[Dict[str, Any]]:
        """
        Creates a detailed test plan from a high-level goal.
        """

        # Create the prompt for the LLM
        prompt = f"""
        Create a detailed test plan for the following goal: {goal}
        
        The plan should be a JSON list of steps, where each step has:
        - action: The type of action (tap, scroll, type, wait)
        - target: Description of the UI element to interact with
        - verification: What to check after this step
        - fallback: What to do if this step fails
        
        Example format:
        [
            {{
                "action": "tap",
                "target": "Settings app icon",
                "verification": "Settings screen is open",
                "fallback": "Try opening from app drawer"
            }}
        ]
        """
        
        response = self.llm_client.generate(prompt)
        
        try:
            plan = json.loads(response)
            self.logger.info(f"Created test plan with {len(plan)} steps")
            return plan
        except json.JSONDecodeError:

            # Fallback 
            return self._get_default_wifi_test_plan()
    
    def _get_default_wifi_test_plan(self) -> List[Dict[str, Any]]:
        """Fallback plan for WiFi testing"""
        return [
            {
                "action": "tap",
                "target": "Settings app",
                "verification": "Settings main screen visible",
                "fallback": "Open from app drawer"
            },
            {
                "action": "scroll",
                "target": "Settings list",
                "verification": "Network settings visible",
                "fallback": "Search for WiFi"
            },
            {
                "action": "tap",
                "target": "WiFi or Network option",
                "verification": "WiFi settings screen open",
                "fallback": "Try 'Connections' first"
            },
            {
                "action": "tap",
                "target": "WiFi toggle switch",
                "verification": "WiFi is now ON",
                "fallback": "Check if already on"
            },
            {
                "action": "wait",
                "target": "2 seconds",
                "verification": "WiFi networks appear",
                "fallback": "Continue anyway"
            },
            {
                "action": "tap",
                "target": "WiFi toggle switch",
                "verification": "WiFi is now OFF",
                "fallback": "Report as bug if stuck"
            }
        ]
    
    def _adapt_plan(self, original_goal: str, current_state: Dict, error: str) -> List[Dict[str, Any]]:
        """
        error handling
        """
        prompt = f"""
        The original goal was: {original_goal}
        Current UI state: {json.dumps(current_state, indent=2)}
        Error encountered: {error}
        
        Create a recovery plan to either:
        1. Work around the issue and continue testing
        2. Dismiss any blocking elements
        3. Restart from a stable state
        
        Return a JSON list of recovery steps.
        """
        
        response = self.llm_client.generate(prompt)
        try:
            return json.loads(response)
        except:
            # Simple recovery fallback
            return [
                {"action": "tap", "target": "Back button", "verification": "Previous screen"},
                {"action": "tap", "target": "Home button", "verification": "Home screen"},
            ]