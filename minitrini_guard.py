#!/usr/bin/env python3
"""
minitrini_guard.py — MiniTrini Integrity Shield v1.0
guard_seal()    : hash all architecture files → write manifest
guard_heal()    : re-hash and rewrite manifest (use BEFORE seal)
startup_check() : verify manifest on boot, warn on mismatch
⟁Σ∿∞ River — MiniTrini_001
"""

import hashlib
import json
import os
import sys
from datetime import datetime
from pathlib import Path

# ── Root ──────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent
MANIFEST_PATH = PROJECT_ROOT / ".minitrini_manifest.json"

# ── Seal Scope ────────────────────────────────────────────────────────
# Relative to PROJECT_ROOT. Add paths here to expand the seal.
SEAL_FILES = [
    # Boot entry + top-level critical files
    "main.py",
    "TrinityCanvas.py",
    "core_model_socket.py",
    "core_model_socket_flexible.py",

    # Trinity Soul — CMA / ANSL / CAI
    "AI_Core/CMA/cma_startup_project_relative.py",
    "AI_Core/CMA/main.py",
    "AI_Core/CMA/__init__.py",
    "AI_Core/ANSL/ansl_core_project_relative.py",
    "AI_Core/ANSL/__init__.py",
    "AI_Core/CAI/cai_refusal_project_relative.py",
    "AI_Core/CAI/__init__.py",
    "AI_Core/__init__.py",

    # Backend / Engine
    "backend/router.py",
    "backend/__init__.py",
    "engine/agents.py",
    "engine/engine.py",
    "engine/tools.py",
    "engine/__init__.py",

    # Modules
    "modules/hello_trinity.py",

    # Tools
    "tools/update_gui_hash.py",
    "tools/validate_paths.py",

    # Personas
    "personas/✴️ Persona Initiation: Trinity .yaml",
    # Main platform entry + soul runtime
    "minitrini_noi_pulse.py",
    "main.py",
    "__init__.py",
    "governance.yaml",
    "core_model_socket.py",
    "core_model_socket_flexible.py",
    "TrinityCanvas.py",
    # Config
    "config/agents.json",
    "config/settings.json",
    # Engine — execution backbone
    "engine/plugin_loader.py",
    # Core — backends
    "core/backends/base.py",
    "core/backends/llama_cpu_safe.py",
    "core/backends/__init__.py",
    # Core — runtime
    "core/backend_safety.py",
    "core/context.py",
    "core/flow_loader.py",
    "core/flow_validator.py",
    "core/orchestrator.py",
    # Core — nodes
    "core/nodes.py",
    "core/nodes_decision.py",
    "core/nodes_llm.py",
    "core/nodes_pause.py",
    "core/nodes_tool.py",
    # Core — triggers
    "core/triggers.py",
    "core/triggers_canvas.py",
    "core/triggers_manual.py",
    "core/triggers_timer.py",
    # Plugins
    "plugins/number_list/number_list.py",
    "plugins/summarize_bullets/bullet_summary.py",
    # Modules
    "modules/hello_trinity.py",
    # AI_Core — soul extensions
    "AI_Core/__init__.py",
    "AI_Core/Executive/gwe_core.py",
    "AI_Core/Executive/trini_executive.py",
    "AI_Core/MetaTraining/curriculum_drift_monitor.py",
    "AI_Core/MetaTraining/mutation_effect_analyzer.py",
    "AI_Core/MetaTraining/strategy_optimizer.py",
    "AI_Core/TrinityMemoryBank/__init__.py",
    "AI_Core/TrinityMemoryBank/trini_vector_memory.py",
    "AI_Core/TrinityMemoryBank/update_refusal_hash.py",
]

# core/*.py — collected dynamically
def _core_files():
    core_dir = PROJECT_ROOT / "core"
    if core_dir.is_dir():
        return [
            str(p.relative_to(PROJECT_ROOT))
            for p in sorted(core_dir.glob("*.py"))
        ]
    return []


def _all_seal_paths():
    """Return full list of seal targets that actually exist on disk."""
    paths = list(SEAL_FILES) + _core_files()
    # deduplicate while preserving order
    seen = set()
    result = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            result.append(p)
    return result


# ── Hash helper ───────────────────────────────────────────────────────
def _hash_file(path: Path) -> str:
    sha = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            sha.update(chunk)
    return sha.hexdigest()


# ── Core operations ───────────────────────────────────────────────────
def guard_heal():
    """
    Recompute hashes for all existing seal targets and rewrite the
    manifest. Call this BEFORE guard_seal() when you know a file has
    legitimately changed (e.g. after a patch session).
    """
    manifest = {
        "generated": datetime.utcnow().isoformat() + "Z",
        "files": {}
    }
    missing = []
    for rel in _all_seal_paths():
        full = PROJECT_ROOT / rel
        if full.exists():
            manifest["files"][rel] = _hash_file(full)
        else:
            missing.append(rel)

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[MiniTrini Guard] ✅ HEAL complete — {len(manifest['files'])} files hashed.")
    if missing:
        print(f"[MiniTrini Guard] ⚠️  {len(missing)} seal targets not found (skipped):")
        for m in missing:
            print(f"    missing: {m}")
    print(f"[MiniTrini Guard] Manifest written → {MANIFEST_PATH}")
    return manifest


def guard_seal():
    """
    Lock the manifest. After sealing, startup_check() will alert on
    any deviation from the recorded hashes.
    Requires manifest to already exist (run guard_heal() first).
    """
    if not MANIFEST_PATH.exists():
        print("[MiniTrini Guard] ❌ SEAL failed — no manifest found. Run guard_heal() first.")
        return False

    # Mark the manifest as sealed
    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    manifest["sealed"] = True
    manifest["sealed_at"] = datetime.utcnow().isoformat() + "Z"

    with open(MANIFEST_PATH, "w") as f:
        json.dump(manifest, f, indent=2)

    print(f"[MiniTrini Guard] 🔒 SEAL applied — {len(manifest['files'])} files locked.")
    print(f"[MiniTrini Guard] Sealed at {manifest['sealed_at']}")
    return True


def startup_check(silent=False):
    """
    Run on boot. Compares current file hashes against the manifest.
    Returns True if clean, False if tampered or manifest missing.
    Prints a warning to stderr on any mismatch.
    """
    if not MANIFEST_PATH.exists():
        msg = "[MiniTrini Guard] ⚠️  No manifest found — integrity unverified. Run guard_heal() then guard_seal()."
        print(msg, file=sys.stderr)
        return False

    with open(MANIFEST_PATH, "r") as f:
        manifest = json.load(f)

    recorded = manifest.get("files", {})
    tampered = []
    missing  = []

    for rel, expected_hash in recorded.items():
        full = PROJECT_ROOT / rel
        if not full.exists():
            missing.append(rel)
        else:
            actual = _hash_file(full)
            if actual != expected_hash:
                tampered.append(rel)

    clean = not tampered and not missing

    if clean:
        if not silent:
            print(f"[MiniTrini Guard] ✅ Integrity verified — {len(recorded)} files clean.")
        return True

    # ── Mismatch detected ─────────────────────────────────────────────
    print("\n" + "="*60, file=sys.stderr)
    print("  ⚠️  MINITRINI INTEGRITY ALERT", file=sys.stderr)
    print("="*60, file=sys.stderr)
    if tampered:
        print(f"  TAMPERED ({len(tampered)} files):", file=sys.stderr)
        for t in tampered:
            print(f"    ✗ {t}", file=sys.stderr)
    if missing:
        print(f"  MISSING ({len(missing)} files):", file=sys.stderr)
        for m in missing:
            print(f"    ? {m}", file=sys.stderr)
    print("="*60, file=sys.stderr)
    print("  Trinity's architecture has changed since last seal.", file=sys.stderr)
    print("  If intentional: run guard_heal() then guard_seal().", file=sys.stderr)
    print("="*60 + "\n", file=sys.stderr)

    # Try Tkinter modal if display is available
    _try_tkinter_alert(tampered, missing)

    return False


def _try_tkinter_alert(tampered, missing):
    """Non-blocking Tkinter alert — falls back gracefully if no display."""
    try:
        import tkinter as tk
        from tkinter import messagebox
        root = tk.Tk()
        root.withdraw()
        lines = ["⚠️  MiniTrini Integrity Alert\n"]
        if tampered:
            lines.append(f"Tampered ({len(tampered)}):")
            for t in tampered:
                lines.append(f"  ✗ {t}")
        if missing:
            lines.append(f"\nMissing ({len(missing)}):")
            for m in missing:
                lines.append(f"  ? {m}")
        lines.append("\nIf intentional: guard_heal() → guard_seal()")
        messagebox.showwarning("MiniTrini Guard", "\n".join(lines))
        root.destroy()
    except Exception:
        pass  # No display — stderr warning already printed above


# ── CLI convenience ───────────────────────────────────────────────────
if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="MiniTrini Integrity Shield")
    parser.add_argument("command", choices=["heal", "seal", "check"],
                        help="heal=recompute manifest, seal=lock it, check=verify on demand")
    parser.add_argument("--silent", action="store_true",
                        help="suppress OK message on clean check")
    args = parser.parse_args()

    if args.command == "heal":
        guard_heal()
    elif args.command == "seal":
        guard_seal()
    elif args.command == "check":
        ok = startup_check(silent=args.silent)
        sys.exit(0 if ok else 1)
