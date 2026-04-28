# core/backend_safety.py
import platform
import subprocess
from llama_cpp import Llama

def detect_hardware():
    arch = platform.machine().lower()
    flags = set()

    try:
        out = subprocess.check_output(["lscpu"], text=True)
        for line in out.splitlines():
            if line.startswith("Flags:"):
                flags = set(line.split(":")[1].strip().split())
                break
    except Exception:
        pass

    return {
        "arch": arch,
        "is_arm": arch in ("aarch64", "arm64"),
        "is_x86": arch in ("x86_64", "amd64"),
        "avx2": "avx2" in flags,
        "fma": "fma" in flags,
    }


def select_backend(hw):
    if hw["is_arm"]:
        return "ai_hat"

    if hw["is_x86"]:
        if hw["avx2"] and hw["fma"]:
            return "llama_x86_modern"
        return "llama_cpu_safe"

    return "unsupported"


def safe_defaults(backend):
    if backend == "llama_cpu_safe":
        return {
            "n_ctx": 2048,
            "n_threads": 1,
            "use_mmap": False,
            "use_mlock": False,
        }

    if backend == "llama_x86_modern":
        return {
            "n_ctx": 4096,
            "n_threads": 4,
        }

    if backend == "ai_hat":
        return {}

    return {}
