"""
executor agent: performs the actual UI interactions
"""
from typing import Dict, Any, Tuple
import time
from .base_agent import BaseAgent, AgentMessage
from android_env import AndroidEnv

class ExecutorAgent(BaseAgent):


    
    def __init__(self, env: AndroidEnv):
        super().__init__("ExecutorAgent")
        self.env = env
        self.current_observation = None
        
    def process(self, message: AgentMessage) -> AgentMessage:
        if message.message_type == "execute_plan":
            results = self._execute_plan(message.content["plan"])
            return self.send_message(
                recipient="VerifierAgent",
                message_type="verify_execution",
                content={
                    "plan": message.content["plan"],
                    "results": results
                }
            )
    
    def _execute_plan(self, plan: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Executes each step in the test plan and returns results for each step including success/failure and screenshots
        """
        results = []
        
        for step_num, step in enumerate(plan):
            self.logger.info(f"Executing step {step_num + 1}: {step['action']} on {step['target']}")
            
            # Get current screen state
            observation = self.env.observe()
            self.current_observation = observation
            
            # Execute the action based on type
            if step['action'] == 'tap':
                success, details = self._execute_tap(step['target'], observation)
            elif step['action'] == 'scroll':
                success, details = self._execute_scroll(step['target'], observation)
            elif step['action'] == 'type':
                success, details = self._execute_type(step['target'], step.get('text', ''))
            elif step['action'] == 'wait':
                time.sleep(float(step['target'].split()[0]))
                success, details = True, {"waited": step['target']}
            else:
                success, details = False, {"error": f"Unknown action: {step['action']}"}
            
            # Record the result
            result = {
                "step": step,
                "success": success,
                "details": details,
                "screenshot": observation.get('pixels', None),
                "ui_hierarchy": observation.get('ui_tree', None)
            }
            results.append(result)
            
            # If step failed and no fallback, stop execution
            if not success and not step.get('fallback'):
                self.logger.error(f"Step failed with no fallback: {details}")
                break
                
        return results
    
    def _execute_tap(self, target: str, observation: Dict) -> Tuple[bool, Dict]:
        """
        Executes a tap action on the specified target
        """
        # Parse the UI tree to find matching elements
        ui_tree = observation.get('ui_tree', {})
        element = self._find_ui_element(target, ui_tree)
        
        if not element:
            return False, {"error": f"Could not find element: {target}"}
        
        # Get element bounds and calculate tap coordinates
        bounds = element.get('bounds', [])
        if len(bounds) == 4:
            x = (bounds[0] + bounds[2]) // 2
            y = (bounds[1] + bounds[3]) // 2
            
            # Execute the tap
            action = {
                "action_type": "touch",
                "coordinate": [x, y]
            }
            self.env.step(action)
            
            return True, {"tapped_at": [x, y], "element": element.get('text', '')}
        
        return False, {"error": "Invalid element bounds"}
    
    def _find_ui_element(self, target: str, ui_tree: Dict) -> Dict:
        """
        searches the UI tree for an element matching the target description
        """
        target_lower = target.lower()
        
        def search_tree(node):
            # Check if this node matches
            node_text = str(node.get('text', '')).lower()
            node_desc = str(node.get('content-desc', '')).lower()
            node_id = str(node.get('resource-id', '')).lower()
            
            if (target_lower in node_text or 
                target_lower in node_desc or 
                target_lower in node_id):
                return node
            
            # Recursively search children
            for child in node.get('children', []):
                result = search_tree(child)
                if result:
                    return result
            
            return None
        
        return search_tree(ui_tree)
    
    def _execute_scroll(self, target: str, observation: Dict) -> Tuple[bool, Dict]:
        """
        scroll action
        """
        # Simple scroll implementation
        screen_height = observation.get('screen_height', 1920)
        screen_width = observation.get('screen_width', 1080)
        
        # Default to scrolling down
        start_x = screen_width // 2
        start_y = screen_height * 3 // 4
        end_x = screen_width // 2
        end_y = screen_height // 4
        
        action = {
            "action_type": "swipe",
            "start_coordinate": [start_x, start_y],
            "end_coordinate": [end_x, end_y],
            "duration": 500  # milliseconds
        }
        
        self.env.step(action)
        
        return True, {"scrolled": "down", "distance": start_y - end_y}