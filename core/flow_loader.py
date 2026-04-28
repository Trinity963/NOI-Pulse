# core/flow_loader.py

from pathlib import Path
import yaml

from core.nodes_llm import LLMNode
from core.nodes_decision import DecisionNode
from core.nodes_tool import ToolNode
from core.nodes_pause import PauseNode
from core.flow_validator import validate_flow


def load_flow(path, backend, actions, conditions):
    # Resolve path relative to this file (core/)
    flow_path = Path(__file__).parent / path

    with open(flow_path, "r") as f:
        spec = yaml.safe_load(f)

    # Validate before building anything
    validate_flow(spec)

    nodes = {}
    ordered_ids = []

    # First pass: create nodes
    for node in spec["nodes"]:
        node_id = node["id"]
        node_type = node["type"]

        if node_type == "llm":
            n = LLMNode(
                backend,
                input_key=node["input"],
                output_key=node["output"],
                model=node.get("model", None),
            )

        elif node_type == "tool":
            n = ToolNode(actions[node["action"]])

        elif node_type == "decision":
            n = DecisionNode(
                condition_fn=conditions[node["condition"]],
                true_nodes=[],
                false_nodes=[],
            )

        elif node_type == "pause":
            n = PauseNode(
                app=actions.get("__app__"),
                question=node.get("question", "Your input is needed to continue:")
            )
        else:
            raise ValueError(f"Unknown node type: {node_type}")

        nodes[node_id] = n
        ordered_ids.append(node_id)

    # Second pass: wire decision branches
    for node in spec["nodes"]:
        if node["type"] == "decision":
            dec = nodes[node["id"]]
            dec.true_nodes = [nodes[n] for n in node.get("on_true", [])]
            dec.false_nodes = [nodes[n] for n in node.get("on_false", [])]

    return [nodes[nid] for nid in ordered_ids]
