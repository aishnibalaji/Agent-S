# multi_agent_qa/agents/planner_agent.py
"""
Planner Agent - Decomposes high-level QA goals into actionable subgoals
"""

import json
from typing import List, Dict, Any, Optional

class PlannerAgent:
    """
    Agent responsible for:
    1. Parsing high-level QA goals into specific, actionable steps
    2. Dynamic replanning when issues are detected
    """
    
    def __init__(self):
        self.current_plan = []
        self.execution_history = []
    
    def create_qa_plan(self, qa_goal: str) -> List[Dict[str, Any]]:
        """Create initial QA test plan from high-level goal"""
        print(f"Creating QA plan for: {qa_goal}")
        
        if "wifi" in qa_goal.lower():
            return self._create_wifi_toggle_plan()
        elif "alarm" in qa_goal.lower():
            return self._create_alarm_plan()
        else:
            return self._create_generic_plan(qa_goal)
    
    def _create_wifi_toggle_plan(self) -> List[Dict[str, Any]]:
        """Create detailed plan for WiFi toggle testing"""
        plan = [
            {
                "step_id": 1,
                "action": "open_settings_app",
                "description": "Navigate to Android Settings application",
                "expected_result": "Settings app opens with main menu visible",
                "verification_criteria": ["Settings app title visible", "Menu options displayed"],
                "action_type": "navigation",
                "timeout": 10
            },
            {
                "step_id": 2,
                "action": "find_wifi_option",
                "description": "Locate WiFi settings option in Settings menu",
                "expected_result": "WiFi option is visible and clickable",
                "verification_criteria": ["WiFi text visible", "WiFi icon present"],
                "action_type": "locate",
                "timeout": 5
            },
            {
                "step_id": 3,
                "action": "tap_wifi_option",
                "description": "Tap on WiFi settings option",
                "expected_result": "WiFi settings screen opens",
                "verification_criteria": ["WiFi settings title", "Toggle switch visible"],
                "action_type": "touch",
                "timeout": 10
            },
            {
                "step_id": 4,
                "action": "check_current_wifi_state",
                "description": "Determine current WiFi toggle state (on/off)",
                "expected_result": "WiFi state is clearly identifiable",
                "verification_criteria": ["Toggle position clear", "Status text readable"],
                "action_type": "verify",
                "timeout": 3
            },
            {
                "step_id": 5,
                "action": "toggle_wifi_off",
                "description": "Turn WiFi off if currently on",
                "expected_result": "WiFi is disabled",
                "verification_criteria": ["Toggle shows off position", "Status shows disabled"],
                "action_type": "touch",
                "timeout": 15
            },
            {
                "step_id": 6,
                "action": "verify_wifi_off",
                "description": "Confirm WiFi is completely disabled",
                "expected_result": "WiFi functionality is off",
                "verification_criteria": ["No network connections", "Toggle clearly off"],
                "action_type": "verify",
                "timeout": 10
            },
            {
                "step_id": 7,
                "action": "toggle_wifi_on",
                "description": "Turn WiFi back on",
                "expected_result": "WiFi is enabled and scanning",
                "verification_criteria": ["Toggle shows on position", "Networks list appears"],
                "action_type": "touch",
                "timeout": 15
            },
            {
                "step_id": 8,
                "action": "verify_wifi_on",
                "description": "Confirm WiFi is fully functional",
                "expected_result": "WiFi is working normally",
                "verification_criteria": ["Networks visible", "WiFi icon in status bar"],
                "action_type": "verify",
                "timeout": 20
            }
        ]
        
        self.current_plan = plan
        return plan
    
    def _create_alarm_plan(self) -> List[Dict[str, Any]]:
        """Create plan for alarm creation testing"""
        return [
            {
                "step_id": 1,
                "action": "open_clock_app",
                "description": "Open the Clock application",
                "expected_result": "Clock app opens",
                "verification_criteria": ["Clock interface visible"],
                "action_type": "navigation",
                "timeout": 10
            },
            {
                "step_id": 2,
                "action": "navigate_to_alarm_tab",
                "description": "Navigate to alarm section",
                "expected_result": "Alarm interface displayed",
                "verification_criteria": ["Alarm list visible", "Add alarm button present"],
                "action_type": "navigation",
                "timeout": 5
            }
        ]
    
    def _create_generic_plan(self, qa_goal: str) -> List[Dict[str, Any]]:
        """Create generic plan"""
        return [
            {
                "step_id": 1,
                "action": "analyze_goal",
                "description": f"Analyze the goal: {qa_goal}",
                "expected_result": "Goal understood",
                "verification_criteria": ["Clear understanding of requirements"],
                "action_type": "analysis",
                "timeout": 5
            }
        ]
    
    def replan(self, failed_step: Dict[str, Any], error_context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Create new plan when execution fails"""
        print(f"Replanning after step {failed_step.get('step_id')} failed")
        
        failure_type = error_context.get("error_type", "unknown")
        
        # Generate recovery steps based on failure type
        if failure_type == "element_not_found":
            recovery_steps = [
                {
                    "step_id": 99,
                    "action": "take_screenshot",
                    "description": "Capture current screen for analysis",
                    "expected_result": "Screenshot captured",
                    "verification_criteria": ["Image saved"],
                    "action_type": "capture",
                    "timeout": 5
                },
                {
                    "step_id": 100,
                    "action": "identify_current_screen",
                    "description": "Determine what screen we're currently on",
                    "expected_result": "Screen identified",
                    "verification_criteria": ["Screen type determined"],
                    "action_type": "analysis",
                    "timeout": 5
                }
            ]
        else:
            # Generic recovery
            recovery_steps = [
                {
                    "step_id": 99,
                    "action": "go_back",
                    "description": "Go back to previous screen",
                    "expected_result": "Previous screen displayed",
                    "verification_criteria": ["Known screen visible"],
                    "action_type": "navigation",
                    "timeout": 5
                }
            ]
        
        return recovery_steps
    
    def get_plan_summary(self) -> Dict[str, Any]:
        """Get summary of current plan"""
        return {
            "total_steps": len(self.current_plan),
            "executed_steps": len(self.execution_history),
            "remaining_steps": len(self.current_plan) - len(self.execution_history),
            "current_plan": self.current_plan
        }

def test_planner_agent():
    """Test the PlannerAgent"""
    print("Testing PlannerAgent...")
    
    planner = PlannerAgent()
    
    # Test WiFi plan creation
    qa_goal = "Test WiFi toggle functionality"
    plan = planner.create_qa_plan(qa_goal)
    
    print(f"Generated plan with {len(plan)} steps:")
    for step in plan:
        print(f"  Step {step['step_id']}: {step['description']}")
    
    # Test replanning
    failed_step = plan[2]
    error_context = {"error_type": "element_not_found"}
    replan = planner.replan(failed_step, error_context)
    
    print(f"\nGenerated recovery plan with {len(replan)} steps:")
    for step in replan:
        print(f"  Recovery Step {step['step_id']}: {step['description']}")
    
    print("\n✅ PlannerAgent test completed!")

if __name__ == "__main__":
    test_planner_agent()