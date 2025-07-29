"""
verifier agent: checks if each action produced the expected result.
"""

from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentMessage

class VerifierAgent(BaseAgent):
 
    
    def __init__(self, llm_client):
        super().__init__("VerifierAgent", llm_client)
        
    def process(self, message: AgentMessage) -> AgentMessage:
        
        """Process verification requests"""
        if message.message_type == "verify_execution":
            verification_results = self._verify_results(
                message.content["plan"],
                message.content["results"]
            )
            
            # Check if replanning is needed
            if self._needs_replanning(verification_results):
                return self.send_message(
                    recipient="PlannerAgent",
                    message_type="replan_needed",
                    content={
                        "original_goal": message.content.get("original_goal"),
                        "current_state": verification_results[-1]["current_state"],
                        "error": verification_results[-1]["error"]
                    }
                )
            else:
                return self.send_message(
                    recipient="SupervisorAgent",
                    message_type="test_completed",
                    content={
                        "verification_results": verification_results,
                        "overall_status": self._determine_overall_status(verification_results)
                    }
                )
    
    def _verify_results(self, plan: List[Dict], results: List[Dict]) -> List[Dict]:
        """
        Verifies each step's execution with its expected outcome
        """
        verification_results = []
        
        for i, (step, result) in enumerate(zip(plan, results)):
            if not result['success']:
                # Execution failed
                verification = {
                    "step_num": i,
                    "status": "FAILED",
                    "error": result['details'].get('error', 'Unknown error'),
                    "needs_replanning": True
                }
            else:
                # Verify the expected outcome
                verification = self._verify_step_outcome(
                    step['verification'],
                    result['ui_hierarchy'],
                    result.get('screenshot')
                )
                verification['step_num'] = i
                
            verification['current_state'] = result.get('ui_hierarchy', {})
            verification_results.append(verification)
            
        return verification_results
    
    def _verify_step_outcome(self, expected: str, ui_tree: Dict, screenshot) -> Dict:
        """
        utilizes the LLM to  verify if it is the expected outcome 
        """
        prompt = f"""
        Verify if the following expectation was met:
        Expected: {expected}
        
        Current UI tree: {str(ui_tree)[:1000]}  # Truncate for LLM context
        
        Please analyze and return JSON:
        {{
            "status": "PASSED" or "FAILED" or "BUG_DETECTED",
            "reason": "explanation",
            "confidence": 0.0 to 1.0,
            "bug_description": "if bug detected, describe it"
        }}
        """
        
        response = self.llm_client.generate(prompt)
        
        try:
            verification = json.loads(response)
            return verification
        except:
            # Fallback to simple heuristic verification
            return self._heuristic_verification(expected, ui_tree)
    
    def _heuristic_verification(self, expected: str, ui_tree: Dict) -> Dict:
        """
        rule-based verification for fallback
        """
        expected_lower = expected.lower()
        ui_text = self._extract_all_text(ui_tree).lower()
        
        # Check for common verification patterns
        if "visible" in expected_lower or "open" in expected_lower:
            # Check if expected screen/element is visible
            key_words = expected_lower.replace("visible", "").replace("open", "").strip()
            if any(word in ui_text for word in key_words.split()):
                return {"status": "PASSED", "reason": "Expected content found"}
        
        elif "on" in expected_lower or "off" in expected_lower:
            # Check toggle states
            if "wifi is now on" in expected_lower and "on" in ui_text:
                return {"status": "PASSED", "reason": "WiFi toggle is ON"}
            elif "wifi is now off" in expected_lower and "off" in ui_text:
                return {"status": "PASSED", "reason": "WiFi toggle is OFF"}
        
        return {
            "status": "FAILED",
            "reason": "Could not verify expected outcome",
            "confidence": 0.3
        }
    
    def _extract_all_text(self, ui_tree: Dict) -> str:
        "Recursively extract all text from UI tree"
        texts = []
        
        def extract(node):
            if node.get('text'):
                texts.append(node['text'])
            if node.get('content-desc'):
                texts.append(node['content-desc'])
            for child in node.get('children', []):
                extract(child)
        
        extract(ui_tree)
        return ' '.join(texts)
    
    def _needs_replanning(self, verification_results: List[Dict]) -> bool:
       
        for result in verification_results:
            if result.get('needs_replanning', False):
                return True
            if result.get('status') == 'FAILED' and result.get('confidence', 0) > 0.7:
                return True
        return False
    
    def _determine_overall_status(self, verification_results: List[Dict]) -> str:
        statuses = [r.get('status', 'UNKNOWN') for r in verification_results]
        
        if 'BUG_DETECTED' in statuses:
            return 'BUG_DETECTED'
        elif 'FAILED' in statuses:
            return 'FAILED'
        elif all(s == 'PASSED' for s in statuses):
            return 'PASSED'
        else:
            return 'PARTIAL_PASS'