# multi_agent_qa/agents/executor_agent.py
"""
Executor Agent - Executes subgoals in Android UI environment with intelligent element selection
"""

import time
import re
from typing import Dict, Any, List, Optional, Tuple

class ExecutorAgent:
    """
    Agent responsible for:
    1. Executing subgoals from Planner in Android environment
    2. Parsing UI hierarchy and selecting appropriate elements
    3. Performing grounded actions (touch, type, scroll) with smart element detection
    """
    
    def __init__(self, android_env):
        self.android_env = android_env
        self.execution_history = []
        self.current_ui_state = None
        
    def execute_subgoal(self, subgoal: Dict[str, Any], context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Execute a single subgoal from the planner
        
        Args:
            subgoal: Step from planner with action, description, expected_result
            context: Additional context about current state
            
        Returns:
            Execution result with success status, actions taken, UI changes
        """
        print(f"🎯 Executing: {subgoal['description']}")
        
        start_time = time.time()
        
        try:
            # Get current UI state
            self.current_ui_state = self._get_current_ui_state()
            
            # Parse the subgoal to determine what action to take
            action_plan = self._analyze_subgoal(subgoal, self.current_ui_state)
            
            if not action_plan:
                return self._create_execution_result(
                    success=False,
                    error="Could not determine action plan for subgoal",
                    subgoal=subgoal,
                    duration=time.time() - start_time
                )
            
            # Execute the action plan
            execution_result = self._execute_action_plan(action_plan, subgoal)
            
            # Record execution in history
            self.execution_history.append({
                "subgoal": subgoal,
                "action_plan": action_plan,
                "result": execution_result,
                "timestamp": time.time()
            })
            
            execution_result["duration"] = time.time() - start_time
            return execution_result
            
        except Exception as e:
            return self._create_execution_result(
                success=False,
                error=f"Execution exception: {str(e)}",
                subgoal=subgoal,
                duration=time.time() - start_time
            )
    
    def _analyze_subgoal(self, subgoal: Dict[str, Any], ui_state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Analyze subgoal and current UI to determine the best action plan
        """
        action = subgoal.get("action", "").lower()
        action_type = subgoal.get("action_type", "").lower()
        description = subgoal.get("description", "").lower()
        
        # Navigation actions
        if action_type == "navigation" or "open" in action or "navigate" in action:
            return self._plan_navigation_action(action, description, ui_state)
        
        # Touch/tap actions
        elif action_type == "touch" or "tap" in action or "click" in action:
            return self._plan_touch_action(action, description, ui_state)
        
        # Verification actions
        elif action_type == "verify" or "verify" in action or "check" in action:
            return self._plan_verification_action(action, description, ui_state)
        
        # Input actions
        elif action_type == "input" or "type" in action or "enter" in action:
            return self._plan_input_action(action, description, ui_state)
        
        # Locate actions
        elif action_type == "locate" or "find" in action:
            return self._plan_locate_action(action, description, ui_state)
        
        else:
            print(f"⚠️  Unknown action type: {action_type} for action: {action}")
            return None
    
    def _plan_navigation_action(self, action: str, description: str, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """Plan navigation-based actions"""
        
        if "settings" in action or "settings" in description:
            # Look for Settings app icon or Settings text
            settings_element = self._find_element_by_criteria(ui_state, [
                {"text_contains": "settings"},
                {"text_contains": "Settings"},
                {"id_contains": "settings"}
            ])
            
            if settings_element:
                return {
                    "action_type": "touch",
                    "target_element": settings_element,
                    "coordinates": self._get_element_center(settings_element),
                    "description": "Tap Settings app/option"
                }
        
        elif "home" in action:
            return {
                "action_type": "home",
                "description": "Press home button"
            }
        
        elif "back" in action:
            return {
                "action_type": "back", 
                "description": "Press back button"
            }
        
        return None
    
    def _plan_touch_action(self, action: str, description: str, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """Plan touch/tap actions"""
        
        # Extract what we're trying to tap from the description
        target_keywords = []
        
        if "wifi" in action or "wifi" in description:
            target_keywords.extend(["wifi", "wi-fi", "wireless"])
        
        if "toggle" in action or "switch" in description:
            target_keywords.extend(["toggle", "switch"])
        
        if "button" in description:
            target_keywords.extend(["button"])
        
        # Find the best matching element
        target_element = self._find_element_by_criteria(ui_state, [
            {"text_contains": keyword} for keyword in target_keywords
        ] + [
            {"id_contains": keyword} for keyword in target_keywords
        ])
        
        if target_element:
            return {
                "action_type": "touch",
                "target_element": target_element,
                "coordinates": self._get_element_center(target_element),
                "description": f"Tap {target_element.get('text', 'element')}"
            }
        
        # Fallback: use approximate coordinates based on action type
        return self._get_fallback_coordinates(action, description)
    
    def _plan_verification_action(self, action: str, description: str, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """Plan verification actions"""
        return {
            "action_type": "screenshot",
            "description": "Take screenshot for verification",
            "verification_criteria": self._extract_verification_criteria(description)
        }
    
    def _plan_input_action(self, action: str, description: str, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """Plan text input actions"""
        # Find text input fields
        input_element = self._find_element_by_criteria(ui_state, [
            {"type": "EditText"},
            {"type": "TextField"},
            {"class_contains": "EditText"}
        ])
        
        # Extract text to type (would need to be passed in subgoal)
        text_to_type = "test text"  # This should come from subgoal parameters
        
        if input_element:
            return {
                "action_type": "type",
                "target_element": input_element,
                "text": text_to_type,
                "description": f"Type '{text_to_type}' into input field"
            }
        
        return None
    
    def _plan_locate_action(self, action: str, description: str, ui_state: Dict[str, Any]) -> Dict[str, Any]:
        """Plan element location actions"""
        return {
            "action_type": "screenshot",
            "description": "Take screenshot to locate elements",
            "locate_target": self._extract_locate_target(description)
        }
    
    def _find_element_by_criteria(self, ui_state: Dict[str, Any], criteria_list: List[Dict[str, str]]) -> Optional[Dict[str, Any]]:
        """
        Find UI element matching any of the given criteria
        
        Args:
            ui_state: Current UI state with elements
            criteria_list: List of criteria dicts like {"text_contains": "wifi"}
        
        Returns:
            Best matching UI element or None
        """
        elements = ui_state.get("ui_elements", [])
        
        for criterion in criteria_list:
            for element in elements:
                if self._element_matches_criterion(element, criterion):
                    return element
        
        return None
    
    def _element_matches_criterion(self, element: Dict[str, Any], criterion: Dict[str, str]) -> bool:
        """Check if element matches a specific criterion"""
        
        if "text_contains" in criterion:
            text = element.get("text", "").lower()
            return criterion["text_contains"].lower() in text
        
        elif "id_contains" in criterion:
            element_id = element.get("id", "").lower()
            return criterion["id_contains"].lower() in element_id
        
        elif "class_contains" in criterion:
            class_name = element.get("class", "").lower()
            return criterion["class_contains"].lower() in class_name
        
        elif "type" in criterion:
            element_type = element.get("type", "")
            return element_type == criterion["type"]
        
        return False
    
    def _get_element_center(self, element: Dict[str, Any]) -> Tuple[int, int]:
        """Get center coordinates of UI element"""
        bounds = element.get("bounds", [0, 0, 100, 100])
        
        if len(bounds) >= 4:
            # bounds format: [left, top, right, bottom]
            center_x = (bounds[0] + bounds[2]) // 2
            center_y = (bounds[1] + bounds[3]) // 2
            return (center_x, center_y)
        
        # Fallback to middle of screen
        return (400, 400)
    
    def _get_fallback_coordinates(self, action: str, description: str) -> Dict[str, Any]:
        """Get fallback coordinates when element detection fails"""
        
        # Hardcoded coordinates based on common Android layouts
        if "settings" in action.lower():
            return {
                "action_type": "touch",
                "coordinates": [200, 400],  # Settings app icon location
                "description": "Tap Settings (fallback coordinates)"
            }
        
        elif "wifi" in action.lower():
            return {
                "action_type": "touch", 
                "coordinates": [300, 300],  # WiFi option in Settings
                "description": "Tap WiFi option (fallback coordinates)"
            }
        
        elif "toggle" in action.lower():
            return {
                "action_type": "touch",
                "coordinates": [700, 200],  # Toggle switch location
                "description": "Tap toggle switch (fallback coordinates)"
            }
        
        else:
            return {
                "action_type": "touch",
                "coordinates": [400, 400],  # Center of screen
                "description": "Tap center of screen (fallback)"
            }
    
    def _execute_action_plan(self, action_plan: Dict[str, Any], subgoal: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the determined action plan"""
        
        try:
            # Prepare Android environment action
            android_action = {
                "action_type": action_plan["action_type"]
            }
            
            # Add action-specific parameters
            if action_plan["action_type"] == "touch":
                android_action["coordinates"] = action_plan["coordinates"]
            
            elif action_plan["action_type"] == "type":
                android_action["text"] = action_plan["text"]
            
            elif action_plan["action_type"] == "screenshot":
                pass  # No additional parameters needed
            
            # Execute in Android environment
            env_result = self.android_env.step(android_action)
            
            # Analyze the result
            action_success = env_result.get("action_result", {}).get("success", False)
            
            if action_success:
                return self._create_execution_result(
                    success=True,
                    subgoal=subgoal,
                    action_plan=action_plan,
                    env_result=env_result,
                    message="Action executed successfully"
                )
            else:
                error_msg = env_result.get("action_result", {}).get("error", "Unknown error")
                return self._create_execution_result(
                    success=False,
                    subgoal=subgoal,
                    action_plan=action_plan,
                    env_result=env_result,
                    error=f"Android action failed: {error_msg}"
                )
                
        except Exception as e:
            return self._create_execution_result(
                success=False,
                subgoal=subgoal,
                action_plan=action_plan,
                error=f"Action execution exception: {str(e)}"
            )
    
    def _get_current_ui_state(self) -> Dict[str, Any]:
        """Get current UI state from Android environment"""
        # This would get the latest observation from android_env
        # For now, use the current observation if available
        if hasattr(self.android_env, 'current_observation') and self.android_env.current_observation:
            return self.android_env.current_observation
        
        # Fallback: try to get fresh observation
        return {"ui_elements": [], "activity_info": {}}
    
    def _extract_verification_criteria(self, description: str) -> List[str]:
        """Extract what to verify from description"""
        criteria = []
        
        if "wifi" in description.lower():
            criteria.extend(["WiFi toggle visible", "WiFi status clear"])
        
        if "settings" in description.lower():
            criteria.extend(["Settings screen visible", "Menu options present"])
        
        if "toggle" in description.lower():
            criteria.extend(["Toggle switch state clear"])
        
        return criteria if criteria else ["UI state verification"]
    
    def _extract_locate_target(self, description: str) -> str:
        """Extract what element to locate from description"""
        if "wifi" in description.lower():
            return "WiFi option"
        elif "settings" in description.lower():
            return "Settings elements"
        else:
            return "Target element"
    
    def _create_execution_result(self, success: bool, subgoal: Dict[str, Any], 
                               action_plan: Dict[str, Any] = None, env_result: Dict[str, Any] = None,
                               message: str = "", error: str = "", duration: float = 0) -> Dict[str, Any]:
        """Create standardized execution result"""
        
        result = {
            "success": success,
            "subgoal_id": subgoal.get("step_id", 0),
            "subgoal_action": subgoal.get("action", ""),
            "timestamp": time.time(),
            "duration": duration
        }
        
        if action_plan:
            result["action_plan"] = action_plan
        
        if env_result:
            result["env_result"] = env_result
        
        if message:
            result["message"] = message
        
        if error:
            result["error"] = error
        
        if success:
            result["ui_state_after"] = self._get_current_ui_state()
        
        return result
    
    def get_execution_summary(self) -> Dict[str, Any]:
        """Get summary of all executions performed"""
        total_executions = len(self.execution_history)
        successful_executions = len([e for e in self.execution_history if e["result"]["success"]])
        
        return {
            "total_executions": total_executions,
            "successful_executions": successful_executions,
            "success_rate": successful_executions / total_executions if total_executions > 0 else 0,
            "recent_executions": self.execution_history[-5:]  # Last 5 executions
        }

def test_executor_agent():
    """Test the ExecutorAgent"""
    print("Testing ExecutorAgent...")
    
    # Mock android environment for testing
    class MockAndroidEnv:
        def __init__(self):
            self.current_observation = {
                "ui_elements": [
                    {"id": "settings_icon", "text": "Settings", "bounds": [100, 200, 200, 300]},
                    {"id": "wifi_option", "text": "WiFi", "bounds": [50, 350, 350, 400]},
                    {"id": "wifi_toggle", "text": "Toggle", "bounds": [300, 100, 400, 150]}
                ]
            }
        
        def step(self, action):
            return {
                "action_result": {"success": True, "action_executed": action},
                "observation": self.current_observation
            }
    
    # Test executor
    mock_env = MockAndroidEnv()
    executor = ExecutorAgent(mock_env)
    
    # Test WiFi-related subgoals
    test_subgoals = [
        {
            "step_id": 1,
            "action": "open_settings_app",
            "description": "Navigate to Android Settings application",
            "action_type": "navigation"
        },
        {
            "step_id": 2,
            "action": "tap_wifi_option",
            "description": "Tap on WiFi settings option",
            "action_type": "touch"
        },
        {
            "step_id": 3,
            "action": "verify_wifi_screen",
            "description": "Verify WiFi settings screen is displayed",
            "action_type": "verify"
        }
    ]
    
    for subgoal in test_subgoals:
        print(f"\n--- Testing Subgoal {subgoal['step_id']} ---")
        result = executor.execute_subgoal(subgoal)
        
        status = "✅ SUCCESS" if result["success"] else "❌ FAILED"
        print(f"Result: {status}")
        print(f"Action: {result.get('subgoal_action', 'N/A')}")
        
        if result["success"]:
            print(f"Message: {result.get('message', 'N/A')}")
        else:
            print(f"Error: {result.get('error', 'N/A')}")
    
    # Test execution summary
    summary = executor.get_execution_summary()
    print(f"\n📊 Execution Summary:")
    print(f"   Total: {summary['total_executions']}")
    print(f"   Successful: {summary['successful_executions']}")
    print(f"   Success Rate: {summary['success_rate']:.1%}")
    
    print("\n✅ ExecutorAgent test completed!")

if __name__ == "__main__":
    test_executor_agent()