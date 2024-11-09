from dataclasses import dataclass
from enum import Enum
from typing import Optional

class StepStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    ERROR = "error"
    WAITING = "waiting"

@dataclass
class Step:
    description: str
    status: StepStatus = StepStatus.PENDING
    error_message: Optional[str] = None

class StepManager:
    def __init__(self):
        self.steps: list[Step] = []
        self.current_step_index: int = -1
    
    def add_step(self, description: str) -> Step:
        """add a new step"""
        step = Step(description=description)
        self.steps.append(step)
        return step
    
    def start_step(self, step: Step):
        """start a step"""
        step.status = StepStatus.RUNNING
        self.current_step_index = self.steps.index(step)
    
    def complete_step(self, step: Step, success: bool = True):
        """complete a step"""
        step.status = StepStatus.SUCCESS if success else StepStatus.ERROR
    
    def set_waiting(self, step: Step):
        """set step to waiting status"""
        step.status = StepStatus.WAITING
    
    @property
    def total_steps(self) -> int:
        return len(self.steps)
    
    @property
    def current_step(self) -> Optional[Step]:
        if 0 <= self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None 