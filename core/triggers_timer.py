# core/triggers_timer.py

import time
from core.triggers import Trigger
from core.context import Context


class TimerTrigger(Trigger):
    def __init__(self, interval_seconds, payload=None, once=False):
        self.interval = interval_seconds
        self.payload = payload or {}
        self.once = once
        self.running = False

    def start(self, callback):
        self.running = True

        while self.running:
            ctx = Context()
            for k, v in self.payload.items():
                ctx.set(k, v)

            callback(ctx)

            if self.once:
                break

            time.sleep(self.interval)

    def stop(self):
        self.running = False
