# engine/plugin_loader.py — Sovereign Plugin Registry
import json
import importlib.util
from pathlib import Path

PLUGIN_DIR = Path(__file__).resolve().parent.parent / "plugins"
_loaded_plugins = {}  # intent -> module


def load_plugins(tools_list):
    """Walk plugins/, load manifests, inject into TOOLS list. Returns count loaded."""
    if not PLUGIN_DIR.exists():
        print("[PluginLoader] No plugins/ directory found.")
        return 0

    loaded = 0
    for plugin_dir in sorted(PLUGIN_DIR.iterdir()):
        if not plugin_dir.is_dir():
            continue
        manifest_path = plugin_dir / "plugin.json"
        if not manifest_path.exists():
            print(f"[PluginLoader] Skipping {plugin_dir.name} — no plugin.json")
            continue
        try:
            with open(manifest_path) as f:
                manifest = json.load(f)

            required = ["name", "icon", "intent", "tone"]
            if not all(k in manifest for k in required):
                print(f"[PluginLoader] Skipping {plugin_dir.name} — missing required fields")
                continue

            # Find the .py entry point
            py_files = list(plugin_dir.glob("*.py"))
            if not py_files:
                print(f"[PluginLoader] Skipping {plugin_dir.name} — no .py file found")
                continue

            # Load module
            py_path = py_files[0]
            spec = importlib.util.spec_from_file_location(manifest["intent"], py_path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            _loaded_plugins[manifest["intent"]] = mod

            # Inject into TOOLS if not already present
            already = any(t["intent"] == manifest["intent"] for t in tools_list)
            if not already:
                tools_list.append({
                    "icon": manifest["icon"],
                    "name": manifest["name"],
                    "intent": manifest["intent"],
                    "tone": manifest["tone"],
                    "plugin": True,
                    "plugin_dir": str(plugin_dir)
                })
                print(f"[PluginLoader] Loaded plugin: {manifest['name']} ({manifest['intent']})")
                loaded += 1
            else:
                print(f"[PluginLoader] Skipping {manifest['name']} — intent already registered")

        except Exception as e:
            print(f"[PluginLoader] Error loading {plugin_dir.name}: {e}")

    return loaded


def run_plugin(intent, tool, user_text):
    """Run a plugin's run() function by intent. Returns transformed text."""
    mod = _loaded_plugins.get(intent)
    if mod and hasattr(mod, "run"):
        return mod.run(tool, user_text)
    return user_text


def unload_plugin(intent, tools_list):
    """Remove plugin from TOOLS list and _loaded_plugins by intent."""
    _loaded_plugins.pop(intent, None)
    before = len(tools_list)
    tools_list[:] = [t for t in tools_list if t.get("intent") != intent]
    return len(tools_list) < before


def list_plugins():
    """Return list of loaded plugin intents."""
    return list(_loaded_plugins.keys())
