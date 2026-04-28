# MiniTrini v10.1 — Multi-Agent Trinity Console

A modular, sovereign AI console for local and cloud-backed LLM inference, multi-agent orchestration, plugin execution, and automation flows. Runs fully offline or against external backends. No cloud dependency required.

---

## Requirements

- Python 3.11+
- Linux (tested on Ubuntu 24.04)
- `tkinterdnd2` — drag-and-drop support
- Ollama (optional) — for local model inference via Ollama backend
- X display (Tkinter UI — no headless)

**CPU note:** Requires AVX instruction support. Ivy Bridge (i7-3xxx) and newer are supported. Pin `torch==2.3.1+cpu` on AVX1-only machines — see [Installation](#installation).

---

## Installation

```bash
git clone https://github.com/Trinity963/MiniTrini_clean.git
cd MiniTrini_clean
python3 -m venv minitrini_env
source minitrini_env/bin/activate
pip install -r requirements.txt
```

**AVX1-only CPUs (no AVX2):**
```bash
pip install torch==2.3.1 --index-url https://download.pytorch.org/whl/cpu
pip install sentence-transformers==2.7.0
```

---

## Boot

```bash
source minitrini_env/bin/activate
python3 minitrini_noi_pulse.py
```

---

## Architecture

```
MiniTrini_clean/
├── minitrini_noi_pulse.py   # Main application — UI, agents, engine wiring
├── TrinityCanvas.py        # Canvas IDE window — file editor, output viewer
├── minitrini_guard.py      # Integrity guard — SHA-256 manifest, heal/seal
├── governance.yaml         # Ethical rule layer — blocks and confirmations
├── backend/
│   └── router.py           # LLM backend router — local, Ollama, external
├── engine/
│   ├── agents.py           # Agent definitions (name, icon, tone, overlay)
│   ├── engine.py           # Chat engine — prompt assembly, response handling
│   ├── plugin_loader.py    # Plugin discovery and execution
│   └── tools.py            # Tool definitions and dispatch
├── core/
│   ├── orchestrator.py     # Flow orchestrator
│   ├── flow_loader.py      # YAML flow loader
│   ├── flows/              # Flow definitions (YAML)
│   └── nodes*.py           # Node types: LLM, tool, decision, pause, canvas
├── AI_Core/
│   ├── TrinityMemoryBank/  # Vector memory (sentence-transformers)
│   ├── CMA/                # Core memory architecture
│   ├── ANSL/               # Autonomous natural system layer
│   └── CAI/                # Cognitive architecture interface
├── plugins/                # Plugin folder — each plugin: folder + plugin.json + .py
├── personas/               # Agent persona YAML files
├── memory/                 # Session memory, canvas exports
├── config/
│   ├── settings.json       # App settings
│   └── agents.json         # Agent config overrides
└── docs/                   # Architecture and module documentation
```

---

## Backends

MiniTrini supports two backend modes toggled via the **Toggle Backend** button:

| Mode | Description |
|------|-------------|
| **Local** | Loads a local GGUF model via llama.cpp |
| **Ollama** | Routes to Ollama running on `localhost:11434` |

Switch backends at runtime. Model list updates automatically on toggle.

---

## Agents

Nine built-in agents selectable from the Agent Manager panel:

| Icon | Name | Role |
|------|------|------|
| 👑 | Trini | Core sovereign intelligence |
| 🧑‍💻 | Developer | Senior engineering mindset |
| 🛡️ | Security | Threat evaluation, hardening |
| 🧠 | Reasoning | Step-by-step problem decomposition |
| 🔍 | Research | Context analysis, mental search |
| 🔧 | Optimizer | Efficiency and quality improvement |
| 🧹 | Refactor | Structure cleanup |
| ⌛ | Memory | History recall and restructuring |
| ⚙️ | System | Command-style task execution |

---

## Features

### Knowledge Graph
Persistent SQLite graph at `~/.minitrini/knowledge_graph.db`. Every conversation turn is logged as a node with edges between sequential turns.

Query with `@kg: <keyword>` — results route to Canvas only, never pollute chat memory.

### Governance Layer
Ethical rule engine loaded from `governance.yaml` at boot. Fires before every user input. Blocks or requests confirmation based on trigger matching.

Append-only ledger at `~/.minitrini/governance_ledger.jsonl`.

### Multi-Agent Orchestration
Prefix `@multi <task>` to decompose a task across multiple agents in parallel via `ThreadPoolExecutor`. Results synthesized and routed to Canvas only.

### Human-in-the-Loop
Model responses containing `@pause: <question>` trigger an amber input box. Execution halts until V provides input. Resume injects context and continues the flow.

### Session Memory
Last 40 turns saved to `~/.minitrini/last_session.json` on close. Last 12 exchanges injected into bootstrap on next boot. Trini wakes with context.

### Feedback & Tone
👍/👎 buttons after every response. Feedback logged to `~/.minitrini/feedback_log.json`. Tone hints derived from feedback and injected into session bootstrap.

### Snapshot & Rollback
Manual snapshot via **Rollback** toolbar button. Auto-snapshot fires before every rollback — current state always preserved. Last 10 snapshots kept at `~/.minitrini/snapshots/`.

### HTTPTrigger
MiniTrini exposes a local HTTP server at `localhost:5005` on boot. Callable by other applications in the ecosystem.

```
POST /trigger    {"message": "...", "agent": "Trini"}
GET  /ping       → {"status": "alive", "app": "MiniTrini", "port": 5005}
```

### TrinityCanvas IDE
Separate window for file editing, code output, and canvas drops. Supports drag-and-drop file loading. Multi-agent and `@kg:` output always routes here.

### Plugins
Drop a folder into `plugins/` containing `plugin.json` + a `.py` file. Loaded automatically at boot via Plugin Manager.

### Integrity Guard
```bash
python3 minitrini_guard.py heal   # Rebuild SHA-256 manifest
python3 minitrini_guard.py seal   # Lock all files
```
Always heal before patching. Always seal after. Never reversed.

---

## Toolbar Reference

| Button | Action |
|--------|--------|
| Profile: BUILD | View/set active agent profile |
| Edit Profile | Edit `~/.minitrini/user_profile.json` |
| Plugins | Open plugin manager |
| Rollback | Restore most recent snapshot (auto-snapshots first) |
| Seal Guard | Run guard heal + seal from UI |
| Canvas | Open TrinityCanvas IDE |
| Run Flow | Execute active flow prompt |

---

## Key File Paths

| Path | Purpose |
|------|---------|
| `~/.minitrini/knowledge_graph.db` | Persistent knowledge graph |
| `~/.minitrini/last_session.json` | Session memory replay |
| `~/.minitrini/feedback_log.json` | Feedback and tone hints |
| `~/.minitrini/snapshots/` | Auto and manual snapshots |
| `~/.minitrini/governance_ledger.jsonl` | Governance event log |
| `~/.minitrini/user_profile.json` | User profile |
| `governance.yaml` | Governance rules (in repo) |
| `.minitrini_manifest.json` | Guard integrity manifest (in repo) |

All `~/.minitrini/` paths are outside the repo and never committed.

---

## Governance Rules

Defined in `governance.yaml`. Each rule has:

```yaml
rules:
  - id: rule_id
    description: Human-readable description shown on block
    triggers: ["trigger string 1", "trigger string 2"]
    action: block   # or: confirm
```

- `block` — input rejected, reason displayed in System chat
- `confirm` — execution paused, V prompted via amber input box

---

## Do Not Modify

| File/Path | Reason |
|-----------|--------|
| `backend/router.py` | Core LLM routing — working, sealed |
| `minitrini_guard.py` | Integrity system — working, sealed |
| `AI_Core/CMA/` | Core memory architecture |
| `AI_Core/ANSL/` | Autonomous system layer |
| `AI_Core/CAI/` | Cognitive interface |
| `core/flows/intro.yaml` | Boot flow — uses on_true/on_false |

---

## License

Sovereign. All rights reserved — Victory Brilliant.
