"""
Main test runner that tests all agents to test WiFi settings
"""
import time
from pathlib import Path
import sys

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from agents.planner_agent import PlannerAgent
from agents.executor_agent import ExecutorAgent
from agents.verifier_agent import VerifierAgent
from agents.supervisor_agent import SupervisorAgent
from agents.base_agent import AgentMessage
from utils.android_helper import AndroidHelper
from utils.logging_utils import TestLogger

# For this example, we'll create a mock LLM client
class MockLLMClient:
    """test LLM for running without API keys"""
    def generate(self, prompt: str) -> str:
        # Return predefined responses based on prompt content
        if "test plan" in prompt.lower():
            return json.dumps([
                {"action": "tap", "target": "Settings", "verification": "Settings screen open"},
                {"action": "tap", "target": "WiFi", "verification": "WiFi settings visible"}
            ])
        elif "verify" in prompt.lower():
            return json.dumps({
                "status": "PASSED",
                "reason": "Expected screen found",
                "confidence": 0.9
            })
        return "{}"

class MultiAgentQASystem:
    """
    coordinates all agents to be able to run 
    """
    
    def __init__(self, use_mock_llm: bool = True):
        # Initialize logger
        self.logger = TestLogger()
        
        # Create Android environment
        print("Creating Android environment...")
        self.env = AndroidHelper.create_environment("settings_wifi")
        
        # Initialize LLM client
        if use_mock_llm:
            self.llm_client = MockLLMClient()
        else:
            # for use with real LLM
            import openai
            self.llm_client = openai.Client(api_key="your-api-key")
        
        # Initialize agents
        print("Initializing agents...")
        self.planner = PlannerAgent(self.llm_client)
        self.executor = ExecutorAgent(self.env)
        self.verifier = VerifierAgent(self.llm_client)
        self.supervisor = SupervisorAgent(self.llm_client)
        
        # Message queue for agent communication
        self.message_queue = []
        
    def run_test(self, test_goal: str):
        """
        Runs a complete test case
        """
        print(f"\nStarting test: {test_goal}")
        self.logger.log_step("System", "test_start", {"goal": test_goal})
        
        # create initial message
        initial_message = AgentMessage(
            sender="System",
            recipient="PlannerAgent",
            message_type="create_plan",
            content={"goal": test_goal},
            timestamp=time.time()
        )
        
        # process the message
        current_message = initial_message
        max_iterations = 10 
        iteration = 0
        
        while iteration < max_iterations:
            iteration += 1
            print(f"\nIteration {iteration}: Processing {current_message.message_type}")
            
            # route message to the appropriate agent
            if current_message.recipient == "PlannerAgent":
                response = self.planner.process(current_message)
            elif current_message.recipient == "ExecutorAgent":
                response = self.executor.process(current_message)
            elif current_message.recipient == "VerifierAgent":
                response = self.verifier.process(current_message)
            elif current_message.recipient == "SupervisorAgent":
                response = self.supervisor.process(current_message)
            elif current_message.recipient == "System":
                #completed test
                print("\nTest completed!")
                self._handle_final_report(response.content)
                break
            else:
                print(f"Unknown recipient: {current_message.recipient}")
                break
            
            # log the interaction
            self.logger.log_step(
                current_message.recipient,
                current_message.message_type,
                {"iteration": iteration}
            )
            
            # takes screenshot after each action
            if current_message.recipient == "ExecutorAgent":
                screenshot = AndroidHelper.capture_screenshot(self.env)
                self.logger.save_screenshot(screenshot, f"step_{iteration}")
            
            current_message = response
            
        print("\nTest execution finished!")
        
    def _handle_final_report(self, report_content: Dict):
        """Handles the final test report from the Supervisor"""
        report = report_content['report']
        improvements = report_content['improvements']
        
        print("\n" + "="*50)
        print("TEST REPORT")
        print("="*50)
        print(f"Overall Status: {report['overall_status']}")
        print(f"Steps Passed: {report['passed_steps']}/{report['total_steps']}")
        
        if report['bugs_found']:
            print(f"\nBugs Found: {len(report['bugs_found'])}")
            for bug in report['bugs_found']:
                print(f"  - {bug.get('bug_description', 'Bug detected')}")
        
        print("\nSuggested Improvements:")
        for imp in improvements:
            print(f"  - [{imp.get('priority', 'medium')}] {imp.get('suggestion', '')}")
        
        # Save report
        self.logger.save_test_report(report)
        
        # Save final supervisor report
        final_report = self.supervisor.generate_final_report()
        self.logger.save_test_report(final_report)

def main():
    """
    Main entry point for running the QA system.
    
    To use with real LLM:
    1. Set use_mock_llm=False
    2. Add your OpenAI API key
    3. Make sure android_world is properly set up
    """
    # Create the QA system
    qa_system = MultiAgentQASystem(use_mock_llm=True)
    
    # Run a test
    qa_system.run_test("Test turning WiFi on and off")
    
    # You can run multiple tests
    # qa_system.run_test("Test connecting to a WiFi network")
    # qa_system.run_test("Test WiFi settings in airplane mode")

if __name__ == "__main__":
    main()