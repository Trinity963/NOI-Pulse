# core/nodes_pause.py
import threading
from core.nodes import Node

class PauseNode(Node):
    name = "pause"

    def __init__(self, app, question="Your input is needed to continue:"):
        self.app = app
        self.question = question

    def run(self, context):
        event = threading.Event()
        self.app._pause_event = event
        self.app._pause_context = context
        # Ask V the question in chat
        self.app.root.after(0, lambda: self.app.display_message(
            "⟁ Flow — Waiting for you", self.question
        ))
        # Block flow thread until V replies
        event.wait(timeout=300)
        # Answer injected by process_user_input into context
        self.app._pause_event = None
        return context
