# core/test_trigger_flow.py

from core.orchestrator import Orchestrator
from core.flow_loader import load_flow
from core.backend_safety import detect_hardware, select_backend, safe_defaults
from core.backends.llama_cpu_safe import LlamaCpuSafeBackend
from core.triggers_manual import ManualTrigger



def main():
    # Backend setup
    hw = detect_hardware()
    backend_name = select_backend(hw)
    config = safe_defaults(backend_name)

    backend = LlamaCpuSafeBackend()
    backend.load(
        model_path="AI_Core/Models/mistral-7b-v0.1.Q4_0.gguf",
        config=config,
    )

    actions = {
        "print_short": lambda ctx: print("SHORT:", ctx["response"]),
        "print_long": lambda ctx: print("LONG:", ctx["response"]),
    }

    conditions = {
        "short_response": lambda ctx: len(ctx["response"]) < 80
    }

    flow_nodes = load_flow(
        "flows/intro.yaml",
        backend,
        actions,
        conditions,
    )

    orch = Orchestrator()
    for n in flow_nodes:
        orch.add_node(n)

    def run_flow(ctx):
        orch.run(ctx)

    trigger = ManualTrigger(
        payload={"prompt": "Introduce yourself in one sentence."}
    )

    trigger.fire(run_flow)


    backend.unload()


if __name__ == "__main__":
    main()
