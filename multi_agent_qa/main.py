# multi_agent_qa/core/android_env_wrapper.py
"""
Android Environment Wrapper - Bridge between multi-agent system and AndroidWorld
"""

import time
import json
import subprocess
from typing import Dict, Any, List, Optional

class AndroidEnvWrapper:
    """
    Wrapper around Android environment for multi-agent QA testing
    Currently uses mock implementation - will be replaced with real AndroidWorld
    """
    
    def __init__(self, task_name: str = "settings_wifi", verbose: bool = True):
        self.task_name = task_name
        self.verbose = verbose
        self.step_count = 0
        self.max_steps = 50
        self.current_observation = None
        self.mock_mode = True  # Set to False when AndroidWorld is working
        
        if self.verbose:
            print(f"AndroidEnvWrapper initialized for task: {task_name}")
            if self.mock_mode:
                print("⚠️  Running in MOCK mode - no real Android interaction")
    
    def reset(self) -> Dict[str, Any]:
        """Reset environment and start new task episode"""
        self.step_count = 0
        
        if self.mock_mode:
            self.current_observation = {
                "screenshot": "mock_screenshot_initial.png",
                "ui_elements": [
                    {"id": "settings_icon", "text": "Settings", "bounds": [100, 200, 200, 300]},
                    {"id": "home_button", "text": "Home", "bounds": [400, 800, 500, 900]}
                ],
                "activity_info": {"current_app": "launcher", "screen_type": "home"},
                "timestamp": time.time(),
                "step_count": 0
            }
        else:
            # Real AndroidWorld implementation would go here
            self.current_observation = self._get_real_android_observation()
        
        if self.verbose:
            print(f"Environment reset for task: {self.task_name}")
            
        return self.current_observation
    
    def step(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute an action in the environment
        
        Args:
            action: Dictionary containing action details
                   e.g., {"action_type": "touch", "coordinates": [x, y]}
        
        Returns:
            Dictionary with observation, action result, done status
        """
        self.step_count += 1
        action_type = action.get("action_type", "unknown")
        
        if self.verbose:
            print(f"Step {self.step_count}: Executing {action_type}")
        
        if self.mock_mode:
            result = self._execute_mock_action(action)
        else:
            result = self._execute_real_action(action)
        
        # Update observation
        self.current_observation = self._get_updated_observation(action, result)
        
        # Check if task is complete
        is_done = self._check_task_completion() or self.step_count >= self.max_steps
        
        response = {
            "observation": self.current_observation,
            "action_result": result,
            "done": is_done,
            "step_count": self.step_count,
            "max_steps": self.max_steps
        }
        
        return response
    
    def _execute_mock_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action in mock mode (for testing without real Android)"""
        action_type = action.get("action_type", "").lower()
        
        # Simulate action execution time
        time.sleep(0.5)
        
        if action_type == "touch":
            coordinates = action.get("coordinates", [0, 0])
            return {
                "success": True,
                "action_executed": action,
                "result": f"Mock touch at coordinates {coordinates}",
                "ui_changed": True
            }
        
        elif action_type == "type":
            text = action.get("text", "")
            return {
                "success": True,
                "action_executed": action,
                "result": f"Mock typed text: '{text}'",
                "ui_changed": True
            }
        
        elif action_type == "back":
            return {
                "success": True,
                "action_executed": action,
                "result": "Mock back button pressed",
                "ui_changed": True
            }
        
        elif action_type == "home":
            return {
                "success": True,
                "action_executed": action,
                "result": "Mock home button pressed",
                "ui_changed": True
            }
        
        elif action_type == "screenshot":
            return {
                "success": True,
                "action_executed": action,
                "result": f"Mock screenshot saved: step_{self.step_count}_screenshot.png",
                "ui_changed": False
            }
        
        else:
            return {
                "success": False,
                "action_executed": action,
                "error": f"Unknown action type: {action_type}",
                "ui_changed": False
            }
    
    def _execute_real_action(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """Execute action using real AndroidWorld (to be implemented)"""
        # This would contain real AndroidWorld integration
        # For now, fall back to mock
        return self._execute_mock_action(action)
    
    def _get_updated_observation(self, action: Dict[str, Any], result: Dict[str, Any]) -> Dict[str, Any]:
        """Get updated observation after action execution"""
        if self.mock_mode:
            # Simulate UI changes based on action
            action_type = action.get("action_type", "")
            
            if action_type == "touch" and "settings" in str(action.get("coordinates", [])):
                # Simulate opening Settings app
                ui_elements = [
                    {"id": "wifi_option", "text": "WiFi", "bounds": [50, 200, 350, 250]},
                    {"id": "bluetooth_option", "text": "Bluetooth", "bounds": [50, 260, 350, 310]},
                    {"id": "back_button", "text": "Back", "bounds": [20, 50, 80, 100]}
                ]
                activity_info = {"current_app": "settings", "screen_type": "settings_main"}
            
            elif "wifi" in str(action.get("coordinates", [])).lower():
                # Simulate WiFi settings screen
                ui_elements = [
                    {"id": "wifi_toggle", "text": "WiFi Toggle", "bounds": [300, 100, 400, 150]},
                    {"id": "network_list", "text": "Available Networks", "bounds": [50, 200, 350, 600]},
                    {"id": "back_button", "text": "Back", "bounds": [20, 50, 80, 100]}
                ]
                activity_info = {"current_app": "settings", "screen_type": "wifi_settings"}
            
            else:
                # Keep current UI elements
                ui_elements = self.current_observation.get("ui_elements", [])
                activity_info = self.current_observation.get("activity_info", {})
            
            return {
                "screenshot": f"mock_screenshot_step_{self.step_count}.png",
                "ui_elements": ui_elements,
                "activity_info": activity_info,
                "timestamp": time.time(),
                "step_count": self.step_count
            }
        else:
            return self._get_real_android_observation()
    
    def _get_real_android_observation(self) -> Dict[str, Any]:
        """Get observation from real Android device (to be implemented)"""
        # This would integrate with AndroidWorld to get real observations
        return {"error": "Real Android observation not implemented yet"}
    
    def _check_task_completion(self) -> bool:
        """Check if the current task is completed"""
        if self.task_name == "settings_wifi":
            # For WiFi task, completion would be verified by checking WiFi state
            # In mock mode, complete after 8 steps (our WiFi plan length)
            return self.step_count >= 8
        
        return False
    
    def get_available_actions(self) -> List[str]:
        """Get list of available action types"""
        return [
            "touch",      # Touch at coordinates
            "type",       # Type text
            "key",        # Press key (back, home, etc.)
            "swipe",      # Swipe gesture
            "back",       # Back button
            "home",       # Home button
            "screenshot"  # Take screenshot
        ]
    
    def save_screenshot(self, filepath: str) -> bool:
        """Save current screenshot to file"""
        try:
            if self.mock_mode:
                # In mock mode, just simulate saving
                if self.verbose:
                    print(f"Mock screenshot saved to: {filepath}")
                return True
            else:
                # Real implementation would save actual screenshot
                return False
        except Exception as e:
            print(f"Failed to save screenshot: {e}")
            return False
    
    def get_ui_elements(self) -> List[Dict[str, Any]]:
        """Get current UI elements"""
        if self.current_observation:
            return self.current_observation.get("ui_elements", [])
        return []
    
    def find_element_by_text(self, text: str) -> Optional[Dict[str, Any]]:
        """Find UI element containing specific text"""
        elements = self.get_ui_elements()
        for element in elements:
            if text.lower() in element.get("text", "").lower():
                return element
        return None
    
    def close(self):
        """Clean up and close the environment"""
        if self.verbose:
            print("AndroidEnvWrapper closed")

def test_android_env_wrapper():
    """Test the AndroidEnvWrapper"""
    print("Testing AndroidEnvWrapper...")
    
    # Test basic functionality
    wrapper = AndroidEnvWrapper(task_name="settings_wifi", verbose=True)
    
    # Reset environment
    obs = wrapper.reset()
    print(f"Reset observation keys: {list(obs.keys())}")
    
    # Test different actions
    actions_to_test = [
        {"action_type": "touch", "coordinates": [150, 250]},  # Touch Settings
        {"action_type": "touch", "coordinates": [200, 225]},  # Touch WiFi
        {"action_type": "touch", "coordinates": [350, 125]},  # Touch WiFi toggle
        {"action_type": "screenshot"}
    ]
    
    for i, action in enumerate(actions_to_test, 1):
        print(f"\n--- Testing Action {i}: {action['action_type']} ---")
        result = wrapper.step(action)
        
        action_result = result["action_result"]
        print(f"Success: {action_result['success']}")
        print(f"Result: {action_result.get('result', 'N/A')}")
        print(f"UI Elements: {len(result['observation']['ui_elements'])}")
        print(f"Done: {result['done']}")
    
    # Test utility functions
    print(f"\nAvailable actions: {wrapper.get_available_actions()}")
    
    elements = wrapper.get_ui_elements()
    print(f"Current UI elements: {len(elements)}")
    
    wifi_element = wrapper.find_element_by_text("WiFi")
    print(f"WiFi element found: {wifi_element is not None}")
    
    wrapper.close()
    print("\n✅ AndroidEnvWrapper test completed!")

if __name__ == "__main__":
    test_android_env_wrapper()