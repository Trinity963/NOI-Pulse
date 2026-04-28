# engine/tools.py



TOOLS = [
    {"icon":"🔧", "name":"Optimize",       "intent":"optimize",        "tone":"precise"},
    {"icon":"🧹", "name":"Refactor",       "intent":"refactor",        "tone":"calm"},
    {"icon":"💬", "name":"Explain",        "intent":"explain",         "tone":"gentle"},
    {"icon":"📝", "name":"Summarize",      "intent":"summarize",       "tone":"structured"},
    {"icon":"📐", "name":"Improve Prompt", "intent":"prompt_improve",  "tone":"neutral"},
    {"icon":"🔍", "name":"Analyze",        "intent":"analyze",         "tone":"analytical"},
    {"icon":"💡", "name":"Expand",         "intent":"expand",          "tone":"creative"},
    {"icon":"✂️", "name":"Reduce",         "intent":"reduce",          "tone":"minimal"},
    {"icon":"🌐", "name":"Web Search",     "intent":"websearch",       "tone":"analytical"},
    {"icon":"📡", "name":"Auto Research",  "intent":"auto_research",   "tone":"structured"},
    {"icon":"🧩", "name":"Module",          "intent":"module",          "tone":"creative"},
    {"icon":"🛡", "name":"Guard Bootstrap", "intent":"guard_bootstrap", "tone":"precise"}
]


def run_tool_logic(tool, user_text):
    intent = tool.get("intent")

    if intent == "summarize":
        return f"Summarize clearly:\n\n{user_text}"
    if intent == "optimize":
        return f"Optimize clarity:\n\n{user_text}"
    if intent == "analyze":
        return f"Analyze step-by-step:\n\n{user_text}"
    if intent == "expand":
        return f"Expand creatively:\n\n{user_text}"
    if intent == "explain":
        return f"Explain in simple terms:\n\n{user_text}"
    if intent == "reduce":
        return f"Compress meaning only:\n\n{user_text}"
    if intent == "prompt_improve":
        return f"Improve this prompt:\n\n{user_text}"

    if intent == "module":
        return f"Design or build a sovereign module for MiniTrini:\n\n{user_text}"
    if intent == "guard_bootstrap":
        return (
            f"Bootstrap a sovereign guard for this project:\n\n{user_text}\n\n"
            "Generate a complete project_guard.py with heal(), seal(), verify() functions.\n"
            "Walk all .py files, SHA-256 hash each, write manifest.json.\n"
            "Wire verify() into __main__ boot block.\n"
            "Output the full file ready to save."
        )
    return user_text