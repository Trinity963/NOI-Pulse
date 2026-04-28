# core/nodes_decision.py
from core.nodes import Node
class DecisionNode(Node):
    def __init__(self, condition_fn, true_nodes=None, false_nodes=None):
        self.condition_fn = condition_fn
        self.true_nodes = true_nodes or []
        self.false_nodes = false_nodes or []
    def run(self, context):
        if self.condition_fn(context):
            for node in self.true_nodes:
                context = node.run(context)
        else:
            for node in self.false_nodes:
                context = node.run(context)
        return None
