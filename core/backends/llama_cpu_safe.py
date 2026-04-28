from llama_cpp import Llama

from core.backends.base import InferenceBackend


class LlamaCpuSafeBackend(InferenceBackend):
    name = "llama_cpu_safe"

    def __init__(self):
        self.llm = None

    def load(self, model_path, config):
        print("[LlamaCpuSafeBackend] loading model...")
        self.llm = Llama(
            model_path=model_path,
            **config,
        )
        print("[LlamaCpuSafeBackend] model loaded")

    def generate(self, prompt, stream=False):
        print("[LlamaCpuSafeBackend] generate()")
        result = self.llm(prompt)
        return result["choices"][0]["text"]

    def unload(self):
        print("[LlamaCpuSafeBackend] unload()")
        self.llm = None
