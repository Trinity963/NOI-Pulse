# engine/engine.py
from engine.tools import TOOLS, run_tool_logic


class MiniTriniEngine:
    def __init__(self, app):
        self.app = app

    def run_chat(self, user_text: str):
        agent_name = self.app.state.get("agent") or "Trini"
        tool_name = self.app.state.get("tool")
        tool_obj = next((x for x in TOOLS if x["name"] == tool_name), None) if tool_name else None

        if tool_obj and tool_obj.get("intent") not in ("web_search",):
            user_text = run_tool_logic(tool_obj, user_text)

        backend_prompt = self.app.build_backend_prompt(agent_name, tool_obj, user_text)
        response_text = self.app.backend_router.send(backend_prompt)

        return response_text