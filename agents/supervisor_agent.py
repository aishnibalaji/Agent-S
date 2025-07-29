"""
supervisor agent: reviews the entire test session and provides insights
"""
import json
from typing import Dict, Any, List
from .base_agent import BaseAgent, AgentMessage

class SupervisorAgent(BaseAgent):

    
    def __init__(self, llm_client):
        super().__init__("SupervisorAgent", llm_client)
        self.test_history = []
        
    def process(self, message: AgentMessage) -> AgentMessage:
        """Process test completion messages"""
        if message.message_type == "test_completed":
            report = self._generate_test_report(message.content)
            self.test_history.append(report)
            
            # Analyze for improvements
            improvements = self._suggest_improvements(report)
            
            return self.send_message(
                recipient="System",
                message_type="test_report",
                content={
                    "report": report,
                    "improvements": improvements
                }
            )
    
    def _generate_test_report(self, test_data: Dict) -> Dict:
        """
        Generates a test report
        - test summary(pass/fail)
        - step by step results
        - screenshots and UI
        """
        verification_results = test_data.get('verification_results', [])
        overall_status = test_data.get('overall_status', 'UNKNOWN')
        
        # Create visual trace if screenshots available
        visual_trace = []
        for result in verification_results:
            if 'screenshot' in result:
                visual_trace.append({
                    'step': result['step_num'],
                    'image': result['screenshot'],
                    'status': result['status']
                })
        
        report = {
            'test_id': f"test_{int(time.time())}",
            'overall_status': overall_status,
            'total_steps': len(verification_results),
            'passed_steps': sum(1 for r in verification_results if r['status'] == 'PASSED'),
            'failed_steps': sum(1 for r in verification_results if r['status'] == 'FAILED'),
            'bugs_found': [r for r in verification_results if r.get('status') == 'BUG_DETECTED'],
            'visual_trace': visual_trace,
            'detailed_results': verification_results
        }
        
        return report
    
    def _suggest_improvements(self, report: Dict) -> List[Dict]:
        """
        uses the LLM to analyze the test report and suggest improvements with reinforced learning
        """
        # Prepare context for LLM analysis
        bugs = report.get('bugs_found', [])
        failed_steps = [r for r in report['detailed_results'] if r['status'] == 'FAILED']
        
        prompt = f"""
        Analyze this test report and suggest improvements:
        
        Overall Status: {report['overall_status']}
        Pass Rate: {report['passed_steps']}/{report['total_steps']}
        
        Bugs Found: {json.dumps(bugs, indent=2) if bugs else 'None'}
        Failed Steps: {json.dumps(failed_steps, indent=2) if failed_steps else 'None'}
        
        Please provide:
        1. Root cause analysis of any failures
        2. Suggestions to make the test more robust
        3. Additional test scenarios to consider
        4. Prompt improvements for better agent performance
        
        Return as JSON list of improvements.
        """
        
        response = self.llm_client.generate(prompt)
        
        try:
            improvements = json.loads(response)
        except:
            improvements = self._generate_default_improvements(report)
            
        return improvements
    
    def _generate_default_improvements(self, report: Dict) -> List[Dict]:
        """fallback improvement suggestions"""
        improvements = []
        
        if report['failed_steps'] > 0:
            improvements.append({
                "type": "robustness",
                "suggestion": "Add wait times between actions for UI to update",
                "priority": "high"
            })
            
        if report['overall_status'] == 'BUG_DETECTED':
            improvements.append({
                "type": "bug_reporting",
                "suggestion": "File detailed bug report with reproduction steps",
                "priority": "high"
            })
            
        improvements.append({
            "type": "coverage",
            "suggestion": "Test edge cases like airplane mode, no network",
            "priority": "medium"
        })
        
        return improvements
    
    def generate_final_report(self) -> Dict:
        """
         creates a final report across all test sessions
        """
        if not self.test_history:
            return {"error": "No tests have been run yet"}
        
        total_tests = len(self.test_history)
        passed_tests = sum(1 for t in self.test_history if t['overall_status'] == 'PASSED')
        bugs_found = sum(len(t.get('bugs_found', [])) for t in self.test_history)
        
        return {
            'total_tests_run': total_tests,
            'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'total_bugs_found': bugs_found,
            'test_history': self.test_history
        }