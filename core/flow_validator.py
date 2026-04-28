# core/flow_validator.py

def validate_flow(spec):
    ids = {n["id"] for n in spec["nodes"]}

    for node in spec["nodes"]:
        if node["type"] == "decision":
            for target in node.get("true", []) + node.get("false", []):
                if target not in ids:
                    raise ValueError(
                        f"Decision node '{node['id']}' "
                        f"references unknown node '{target}'"
                    )
