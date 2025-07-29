"""
Base class for all agents in QA system.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import logging
from dataclasses import dataclass

@dataclass
class AgentMessage:
    sender: str
    recipient: str
    message_type: str
    content: Dict[str, Any]
    timestamp: float

class BaseAgent(ABC):
    """
    Abstract base class for all QA agents
    """
    
    def __init__(self, name: str, llm_client=None):
        self.name = name
        self.llm_client = llm_client
        self.message_history: List[AgentMessage] = []
        self.logger = logging.getLogger(name)
        
    @abstractmethod
    def process(self, message: AgentMessage) -> AgentMessage:
        pass
    
    def send_message(self, recipient: str, message_type: str, content: Dict[str, Any]) -> AgentMessage:
        """create and send messages to other agents"""
        import time
        msg = AgentMessage(
            sender=self.name,
            recipient=recipient,
            message_type=message_type,
            content=content,
            timestamp=time.time()
        )
        self.message_history.append(msg)
        return msg