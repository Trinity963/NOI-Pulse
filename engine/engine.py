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

        # Vision — extract base64 images from canvas_context if present
        _images = None
        _canvas_ctx = getattr(self.app, "_canvas_context", {})
        if _canvas_ctx:
            _b64_list = [
                v["base64"] for v in _canvas_ctx.values()
                if isinstance(v, dict) and v.get("type") == "image" and v.get("base64")
            ]
            if _b64_list:
                _images = _b64_list
                print(f"[Engine] Vision — {len(_images)} image(s) from canvas_context", flush=True)

        response_text = self.app.backend_router.send(backend_prompt, images=_images)

        return response_text