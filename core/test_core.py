# core/test_core.py
from backends.llama_cpu_safe import LlamaCpuSafeBackend

from backend_safety import (
    detect_hardware,
    select_backend,
    safe_defaults,
)
from orchestrator import Orchestrator

# Temporary stub backend for testing (NO llama yet)


def load(self, model_path=None, config=None):
    print("[DummyBackend] load() called")
    print("  model_path:", model_path)
    print("  config:", config)

    def generate(self, prompt, stream=False):
        print("[DummyBackend] generate() called")
        print("  prompt:", prompt)
        return "Dummy response"

    def unload(self):
        print("[DummyBackend] unload() called")


def main():
    print("=== MiniTrini Core Test ===")

    hw = detect_hardware()
    print("\n[Hardware Detection]")
    for k, v in hw.items():
        print(f"  {k}: {v}")

    backend_name = select_backend(hw)
    print("\n[Backend Selection]")
    print("  selected:", backend_name)

    config = safe_defaults(backend_name)
    print("\n[Safe Defaults]")
    print(" ", config)

    backend = LlamaCpuSafeBackend()
    backend.load(
        model_path="AI_Core/Models/mistral-7b-v0.1.Q4_0.gguf",
        config=config,
    )


    orch = Orchestrator(backend)
    result = orch.run_llm("Hello MiniTrini")

    print("\n[Orchestrator Result]")
    print(" ", result)

    backend.unload()

    print("\n=== Core test completed successfully ===")


if __name__ == "__main__":
    main()
