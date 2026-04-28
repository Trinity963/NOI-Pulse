# core/triggers.py

class Trigger:
    """
    Base class for all triggers.
    """

    def start(self, callback):
        """
        Start the trigger.
        When fired, must call: callback(context)
        """
        raise NotImplementedError
