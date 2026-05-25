"""
Voice engine for spoken alerts and state announcements.

Uses pyttsx3 for text-to-speech synthesis of system state changes
and important events.
"""

import pyttsx3
import threading
import time
from typing import Optional
from collections import deque
from dataclasses import dataclass

from src.core.classifier import ReactionState
from src.config.settings import VoiceConfig


@dataclass
class VoiceAlert:
    """Voice alert message."""
    message: str
    priority: int  # 0=low, 1=medium, 2=high
    timestamp: float


class VoiceEngine:
    """
    Text-to-speech engine for system announcements.
    
    Provides spoken feedback for state changes and important events
    with cooldown to prevent excessive announcements.
    """
    
    def __init__(self, config: Optional[VoiceConfig] = None):
        """
        Initialize voice engine.
        
        Args:
            config: Voice configuration
        """
        self.config = config or VoiceConfig()
        
        # TTS engine
        self.engine: Optional[pyttsx3.Engine] = None
        self.initialized = False
        
        # Alert queue
        self.alert_queue: deque = deque()
        self.queue_lock = threading.Lock()
        
        # Cooldown tracking
        self.last_alert_time: float = 0.0
        self.last_state: Optional[ReactionState] = None
        
        # Thread control
        self.running = False
        self.thread: Optional[threading.Thread] = None
    
    def initialize(self) -> bool:
        """
        Initialize TTS engine.
        
        Returns:
            True if successful, False otherwise
        """
        if not self.config.ENABLED:
            return False
        
        try:
            self.engine = pyttsx3.init()
            
            # Configure voice
            voices = self.engine.getProperty('voices')
            if voices and len(voices) > self.config.VOICE_INDEX:
                self.engine.setProperty('voice', voices[self.config.VOICE_INDEX].id)
            
            self.engine.setProperty('rate', self.config.RATE)
            self.engine.setProperty('volume', self.config.VOLUME)
            
            self.initialized = True
            return True
        
        except Exception as e:
            print(f"Failed to initialize voice engine: {e}")
            return False
    
    def start(self) -> None:
        """Start voice engine thread."""
        if not self.initialized or self.running:
            return
        
        self.running = True
        self.thread = threading.Thread(target=self._process_queue, daemon=True)
        self.thread.start()
    
    def stop(self) -> None:
        """Stop voice engine thread."""
        self.running = False
        if self.thread:
            self.thread.join(timeout=2.0)
    
    def announce_state(self, state: ReactionState, severity: float = 0.0) -> None:
        """
        Announce state change.
        
        Args:
            state: New reaction state
            severity: Severity level (0-1)
        """
        if not self.config.ENABLED or not self.config.ANNOUNCE_STATE_CHANGES:
            return
        
        # Check cooldown
        current_time = time.time()
        if current_time - self.last_alert_time < self.config.ALERT_COOLDOWN:
            return
        
        # Only announce if state changed
        if state == self.last_state:
            return
        
        # Generate message
        message = self._generate_state_message(state, severity)
        
        # Queue alert
        self._queue_alert(message, priority=1)
        
        # Update tracking
        self.last_alert_time = current_time
        self.last_state = state
    
    def announce_event(self, message: str, priority: int = 1) -> None:
        """
        Announce custom event.
        
        Args:
            message: Message to speak
            priority: Alert priority (0=low, 1=medium, 2=high)
        """
        if not self.config.ENABLED:
            return
        
        # Check cooldown for low priority events
        if priority == 0:
            current_time = time.time()
            if current_time - self.last_alert_time < self.config.ALERT_COOLDOWN:
                return
        
        self._queue_alert(message, priority)
        self.last_alert_time = time.time()
    
    def _queue_alert(self, message: str, priority: int) -> None:
        """Queue alert for processing."""
        with self.queue_lock:
            alert = VoiceAlert(
                message=message,
                priority=priority,
                timestamp=time.time()
            )
            
            # Insert based on priority
            if priority == 2:  # High priority - front of queue
                self.alert_queue.appendleft(alert)
            else:
                self.alert_queue.append(alert)
    
    def _process_queue(self) -> None:
        """Process alert queue in background thread."""
        while self.running:
            if not self.alert_queue.empty():
                with self.queue_lock:
                    if self.alert_queue:
                        alert = self.alert_queue.popleft()
                        self._speak(alert.message)
            
            time.sleep(0.1)
    
    def _speak(self, message: str) -> None:
        """Speak message using TTS engine."""
        if not self.initialized or not self.engine:
            return
        
        try:
            self.engine.say(message)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Error speaking message: {e}")
    
    def _generate_state_message(self, state: ReactionState, severity: float) -> str:
        """
        Generate state announcement message.
        
        Args:
            state: Reaction state
            severity: Severity level
        
        Returns:
            Message to speak
        """
        messages = {
            ReactionState.STABLE: "Reaction stable.",
            ReactionState.TRANSITIONAL: "Reaction transitioning.",
            ReactionState.CRITICAL: "Warning. Critical instability detected.",
            ReactionState.CHAOTIC: "Alert. Chaotic conditions."
        }
        
        base_message = messages.get(state, "Unknown state.")
        
        # Add severity context for critical states
        if state in [ReactionState.CRITICAL, ReactionState.CHAOTIC]:
            if severity > 0.7:
                base_message += " High severity."
        
        return base_message
    
    def is_enabled(self) -> bool:
        """Check if voice engine is enabled."""
        return self.config.ENABLED
    
    def get_queue_size(self) -> int:
        """Get current queue size."""
        with self.queue_lock:
            return len(self.alert_queue)
    
    def clear_queue(self) -> None:
        """Clear alert queue."""
        with self.queue_lock:
            self.alert_queue.clear()
    
    def reset_tracking(self) -> None:
        """Reset state tracking."""
        self.last_alert_time = 0.0
        self.last_state = None
