# core/triggers_manual.py

from core.triggers import Trigger
from core.context import Context


class ManualTrigger(Trigger):
    def __init__(self, payload=None):
        self.payload = payload or {}

    def fire(self, callback):
        ctx = Context()
        for k, v in self.payload.items():
            ctx.set(k, v)

        callback(ctx)
