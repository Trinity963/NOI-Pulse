# core/nodes_tool.py

from core.nodes import Node

class ToolNode(Node):
    """
    Executes a side-effect function.
    """

    def __init__(self, tool_fn):
        self.tool_fn = tool_fn

    def run(self, context):
        self.tool_fn(context)
        return context
