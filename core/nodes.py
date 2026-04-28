# core/nodes.py

class Node:
    """
    Base class for all orchestration nodes.
    """
    name = "node"

    def run(self, context):
        """
        Execute the node.
        Must return context (modified or not).
        """
        raise NotImplementedError
