# core/context.py

class Context(dict):
    """
    Shared state passed between nodes.
    """
    def set(self, key, value):
        self[key] = value

    def get(self, key, default=None):
        return super().get(key, default)
