import curses
import time
import threading
from typing import Optional
from .step_manager import StepManager, StepStatus, Step

class ProgressBar:
    def __init__(self, stdscr, start_y: int = 1):
        self.stdscr = stdscr
        self.start_y = start_y
        self.start_time = time.time()
        self.step_manager = StepManager()
        self.running = True
        self.debug_messages = []  # store debug messages
        
        # start animation thread
        self.animation_thread = threading.Thread(target=self._animate)
        self.animation_thread.daemon = True
        self.animation_thread.start()
    
    def add_debug(self, message: str, error: bool = False):
        """add debug message to log"""
        timestamp = time.strftime('%H:%M:%S')
        self.debug_messages.append((f"[{timestamp}] {message}", error))  # store message with error flag
        if len(self.debug_messages) > 15:
            self.debug_messages.pop(0)
    
    def _animate(self):
        """animation loop running in separate thread"""
        anim_chars = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
        idx = 0
        
        while self.running:
            current_step = self.step_manager.current_step
            if current_step and current_step.status == StepStatus.WAITING:
                self._draw_progress(anim_char=anim_chars[idx])
                idx = (idx + 1) % len(anim_chars)
            else:
                self._draw_progress()
            time.sleep(0.1)
    
    def _draw_progress(self, anim_char: Optional[str] = None):
        """draw the progress bar and status"""
        try:
            height, width = self.stdscr.getmaxyx()
            
            # calculate progress
            total_steps = max(1, self.step_manager.total_steps)
            current_step = max(0, self.step_manager.current_step_index + 1)
            progress = current_step / total_steps
            bar_width = width - 10
            filled = int(bar_width * progress)
            
            colors = {
                StepStatus.PENDING: curses.color_pair(4),
                StepStatus.RUNNING: curses.color_pair(3),
                StepStatus.SUCCESS: curses.color_pair(1),
                StepStatus.ERROR: curses.color_pair(2),
                StepStatus.WAITING: curses.color_pair(4)
            }
            
            # clear lines
            self.stdscr.move(self.start_y, 0)
            self.stdscr.clrtoeol()
            self.stdscr.move(self.start_y + 1, 0)
            self.stdscr.clrtoeol()
            
            # get current step status
            current = self.step_manager.current_step
            current_status = current.status if current else StepStatus.PENDING
            
            # draw progress bar
            if current_status == StepStatus.WAITING and anim_char:
                bar = f"[{anim_char} waiting...]"
            else:
                bar = f"[{'=' * filled}{' ' * (bar_width - filled)}]"
            
            percent = f"{int(progress * 100)}%"
            self.stdscr.addstr(self.start_y, 0, bar, colors[current_status])
            self.stdscr.addstr(self.start_y, width - 5, percent)
            
            # draw step description
            elapsed = time.time() - self.start_time
            if current:
                status_text = f"Step {current_step}/{total_steps} ({elapsed:.1f}s): {current.description}"
                self.stdscr.addstr(self.start_y + 1, 2, status_text[:width-3], colors[current_status])
            
            # draw debug section
            debug_start_y = self.start_y + 3
            self.stdscr.addstr(debug_start_y, 2, "Debug Log:", curses.A_BOLD)
            for i, (msg, is_error) in enumerate(self.debug_messages):
                if debug_start_y + i + 1 < height - 1:  # prevent overflow
                    color = curses.color_pair(2) if is_error else curses.color_pair(3)
                    self.stdscr.addstr(debug_start_y + i + 1, 4, msg[:width-2], color)
            
            self.stdscr.refresh()
        except Exception as e:
            print(f"Error drawing progress: {str(e)}")
    
    def add_step(self, description: str) -> Step:
        """add a new step"""
        return self.step_manager.add_step(description)
    
    def start_step(self, step: Step):
        """start a step"""
        self.step_manager.start_step(step)
    
    def complete_step(self, step: Step, success: bool = True):
        """complete a step"""
        self.step_manager.complete_step(step, success)
    
    def set_waiting(self, step: Step):
        """set step to waiting status"""
        self.step_manager.set_waiting(step)
    
    def __del__(self):
        """cleanup on deletion"""
        self.running = False
        if hasattr(self, 'animation_thread'):
            self.animation_thread.join(timeout=1)