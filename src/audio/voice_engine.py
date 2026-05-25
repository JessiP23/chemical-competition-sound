"""
voice_engine.py

State-aware voice narration engine with:
  - Per-state cooldown timers (no repetitive announcements)
  - Contextual message selection based on features
  - Priority queue (critical > transitional > stable)
  - Non-blocking: runs in daemon thread
"""

import pyttsx3
import threading
import time
from collections import defaultdict
from src.config.settings import VOICE_COOLDOWN


class VoiceEngine:
    MESSAGES = {
        "stable": [
            "Reaction stable.",
            "System in equilibrium.",
            "Chemical process nominal.",
        ],
        "transitional_rising": [
            "pH rising. Reaction shifting.",
            "Temperature increasing. Monitor closely.",
            "Transition detected. Tracking signal.",
        ],
        "transitional_falling": [
            "pH falling. Reaction evolving.",
            "System transitioning. Parameters shifting.",
        ],
        "critical": [
            "Warning: instability detected.",
            "Critical threshold exceeded. Stand by.",
            "Anomaly detected in chemical signal.",
        ],
        "chaotic": [
            "Alert: chaotic behavior detected.",
            "Extreme instability. System in chaos.",
            "Chemical signal critically unstable.",
        ],
        "stabilizing": [
            "System stabilizing.",
            "Reaction returning to equilibrium.",
        ],
        "phase_transition": [
            "Phase transition detected.",
            "Reaction entering new stage.",
        ],
    }

    def __init__(self):
        self._engine = None
        self._lock = threading.Lock()
        self._queue = []
        self._last_announced = defaultdict(float)  # state → last time
        self._running = False
        self._thread = None
        self._prev_state = "stable"
        self._msg_index = defaultdict(int)

    def _init_engine(self):
        """Initialize pyttsx3 in the worker thread (required)."""
        self._engine = pyttsx3.init()
        self._engine.setProperty('rate', 160)
        self._engine.setProperty('volume', 0.9)

    def _select_message(self, state: str, features: dict) -> str:
        """Select contextual message, rotating through options."""
        key = state
        if state == "transitional":
            key = "transitional_rising" if features.get("dpH_dt", 0) > 0 else "transitional_falling"

        messages = self.MESSAGES.get(key, self.MESSAGES["stable"])
        idx = self._msg_index[key] % len(messages)
        self._msg_index[key] += 1
        return messages[idx]

    def announce(self, state: str, features: dict, force: bool = False):
        """
        Schedule an announcement.
        Respects cooldown unless force=True.
        """
        now = time.time()
        cooldown = VOICE_COOLDOWN.get(state, 30.0)
        if not force and (now - self._last_announced[state]) < cooldown:
            return

        msg = self._select_message(state, features)
        self._last_announced[state] = now
        with self._lock:
            self._queue.append((state, msg))

    def announce_transition(self, from_state: str, to_state: str, features: dict):
        """Called on every state change. Always speaks on critical/chaotic transitions."""
        force = to_state in ("critical", "chaotic") or \
                (from_state in ("critical", "chaotic") and to_state == "stable")
        if force:
            self.announce(to_state, features, force=True)
        else:
            self.announce(to_state, features)

        # Special "stabilizing" message when coming back from bad state
        if from_state in ("critical", "chaotic") and to_state in ("stable", "transitional"):
            with self._lock:
                msg = self.MESSAGES["stabilizing"][0]
                self._queue.append(("stabilizing", msg))

    def _worker(self):
        self._init_engine()
        while self._running:
            msg_to_say = None
            with self._lock:
                if self._queue:
                    _, msg_to_say = self._queue.pop(0)
            if msg_to_say:
                self._engine.say(msg_to_say)
                self._engine.runAndWait()
            else:
                time.sleep(0.1)

    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._worker, daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
