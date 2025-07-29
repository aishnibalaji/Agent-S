"""
log utilities for tracking test execution and debugging
"""
import json
import time
from pathlib import Path
from typing import Dict, Any
from loguru import logger

class TestLogger:

    
    def __init__(self, log_dir: str = "test_logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create session directory
        self.session_id = f"session_{int(time.time())}"
        self.session_dir = self.log_dir / self.session_id
        self.session_dir.mkdir(exist_ok=True)
        
        # Configure logger
        log_file = self.session_dir / "test_log.json"
        logger.add(
            log_file,
            format="{time} | {level} | {message}",
            serialize=True  # JSON format
        )
        
        self.screenshot_count = 0
        
    def log_step(self, agent_name: str, action: str, details: Dict[str, Any]):
        """Logs a single test step"""
        logger.info({
            "agent": agent_name,
            "action": action,
            "details": details,
            "timestamp": time.time()
        })
    
    def save_screenshot(self, image, step_name: str = None):
        """Saves a screenshot with metadata"""
        if image is None:
            return None
            
        filename = f"screenshot_{self.screenshot_count:04d}"
        if step_name:
            filename += f"_{step_name}"
        filename += ".png"
        
        filepath = self.session_dir / filename
        image.save(filepath)
        
        self.screenshot_count += 1
        
        logger.info({
            "event": "screenshot_saved",
            "filename": filename,
            "step": step_name
        })
        
        return filepath
    
    def save_test_report(self, report: Dict[str, Any]):
        """Saves the final test report"""
        report_file = self.session_dir / "test_report.json"
        
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
            
        logger.info({
            "event": "test_report_saved",
            "status": report.get('overall_status', 'UNKNOWN'),
            "pass_rate": f"{report.get('passed_steps', 0)}/{report.get('total_steps', 0)}"
        })