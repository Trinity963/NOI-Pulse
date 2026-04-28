# core/nodes_llm.py

from core.nodes import Node

class LLMNode(Node):
    name = "llm"

    def __init__(self, backend, input_key="prompt", output_key="response", model=None):
        self.backend = backend
        self.input_key = input_key
        self.output_key = output_key
        self.model = model

    def run(self, context):
        import requests
        prompt = context.get(self.input_key)
        if not prompt:
            raise RuntimeError("LLMNode: No prompt in context")
        if self.model:
            try:
                resp = requests.post(
                    "http://localhost:11434/api/generate",
                    json={"model": self.model, "prompt": prompt, "stream": False},
                    timeout=(5, 120)
                )
                response = resp.json().get("response", "").strip()
            except Exception as e:
                response = f"[LLMNode ERROR] {e}"
        else:
            response = self.backend.generate(prompt)
        context.set(self.output_key, response)
        return context
