# MiniTrini — Tools & Commands Appendix

Complete reference for all prefix commands, toolbar actions, agents, plugins, flows, canvas rules, and key paths.

---

## Prefix Commands

Commands typed directly into the chat input that are intercepted before reaching the LLM.

| Prefix | Syntax | Description |
|--------|--------|-------------|
| `@kg:` | `@kg: <keyword>` | Query the local knowledge graph. Searches all stored conversation turns by keyword. Results route to Canvas only — never to chat or memory. |
| `@multi` | `@multi <task>` | Multi-agent orchestration. Decomposes task via LLM, assigns subtasks to agents, runs in parallel via ThreadPoolExecutor. Output routes to Canvas only. |
| `@pause:` | _(model output only)_ | Not typed by user. When the model includes `@pause: <question>` in its response, execution halts and an amber input box appears. Resume by typing a response and pressing Send. |

---

## Toolbar Buttons

| Button | Function |
|--------|----------|
| **Profile: BUILD** | Displays active agent profile. Click to cycle or select agent. |
| **Edit Profile** | Opens `~/.minitrini/user_profile.json` for direct editing. |
| **Plugins** | Opens Plugin Manager window — lists loaded plugins, load/unload. |
| **Rollback** | Auto-snapshots current `copy13.py` state, then restores most recent snapshot from `~/.minitrini/snapshots/`. Requires restart to apply. |
| **Seal Guard** | Runs `minitrini_guard.py heal` then `minitrini_guard.py seal` as subprocess. Output appears in System chat and pipeline log. |
| **Canvas** | Opens or focuses TrinityCanvas IDE window. |
| **Run Flow** | Executes the flow prompt currently entered in the Flow Prompt field against the active backend. |

---

## Agents

Selectable from the Agent Manager panel (top-left agent selector).

| Icon | Name | Overlay Instruction | Tone |
|------|------|---------------------|------|
| 👑 | **Trini** | Core sovereign intelligence. | balanced |
| 🧑‍💻 | **Developer** | Think like a senior engineer. | analytical |
| 🛡️ | **Security** | Evaluate threats, harden logic. | formal |
| 🧠 | **Reasoning** | Break problems into steps. | neutral |
| 🔍 | **Research** | Search mentally, analyze context. | curious |
| 🔧 | **Optimizer** | Improve efficiency and quality. | precise |
| 🧹 | **Refactor** | Clean messy structure calmly. | calm |
| ⌛ | **Memory** | Recall and restructure history. | gentle |
| ⚙️ | **System** | Execute command-style tasks safely. | neutral |

To add a custom agent, edit `engine/agents.py` — add a dict with `icon`, `name`, `overlay`, `tone`.

---

## Tools

Defined in `engine/tools.py`. Tools are selectable via the tool picker and intercepted in `process_user_input` before the LLM call.

| Intent | Behaviour |
|--------|-----------|
| `web_search` / `websearch` | Opens web results panel for the user's query |
| `module` | Scaffolds a new Canvas module at the given name via `create_module()` |

Custom tools: add a dict to `TOOLS` in `engine/tools.py` with `name`, `intent`, and handler logic in `run_tool_logic()`.

---

## Plugin Spec

Each plugin lives in `plugins/<plugin_name>/` and requires:

```
plugins/
└── my_plugin/
    ├── plugin.json
    └── my_plugin.py
```

**plugin.json minimum spec:**
```json
{
  "name": "My Plugin",
  "version": "1.0",
  "entry": "my_plugin.py",
  "description": "What this plugin does"
}
```

Plugin is auto-detected if:
- Filename contains `plugin_spec`, OR
- First 5 lines of the file contain `[PLUGIN SPEC]`

Plugins are loaded at boot via `engine/plugin_loader.py`.

---

## Flows

Flows are YAML files in `core/flows/`. Loaded by `core/flow_loader.py` and executed by `core/orchestrator.py`.

**Node types:**

| Node | File | Purpose |
|------|------|---------|
| LLM | `nodes_llm.py` | Call the active LLM backend |
| Tool | `nodes_tool.py` | Execute a registered tool |
| Decision | `nodes_decision.py` | Branch on condition — uses `on_true` / `on_false` |
| Pause | `nodes_pause.py` | Halt and wait for user input |
| Canvas | `triggers_canvas.py` | Route output to TrinityCanvas |

**Flow YAML structure:**
```yaml
name: my_flow
steps:
  - id: step1
    type: llm
    prompt: "Summarize: {input}"
    next: step2
  - id: step2
    type: decision
    condition: "contains:error"
    on_true: error_step
    on_false: done_step
```

**Important:** `intro.yaml` uses `on_true`/`on_false` — do not modify.

---

## Canvas Rules

TrinityCanvas IDE (`TrinityCanvas.py`) — two-drop-zone rule:

| Zone | Behaviour |
|------|-----------|
| **Drop Zone 1** | Drop a file to load it into the active canvas tab |
| **Drop Zone 2** | Drop a file to open it as a new tab |

**Output routing rules:**
- `@multi` results → Canvas only (never chat, never memory)
- `@kg:` results → Canvas only (never chat, never memory)
- Normal chat → chat panel only
- Canvas context is injected into the next LLM prompt if populated

**Early-exit-before-read rule:** Canvas tools must check if the file exists and is readable before attempting to load content. Exit early on failure.

---

## Guard Workflow

```bash
# Always in this order — never reversed
python3 minitrini_guard.py heal   # Rebuild SHA-256 manifest for all 43 files
python3 minitrini_guard.py seal   # Lock all files read-only

# Or from inside the UI:
# Click "Seal Guard" button → runs heal then seal automatically
```

**Rules:**
- Always `heal` before patching any file
- Always `seal` after patching
- Never `seal` before `heal`
- Manifest written to `.minitrini_manifest.json` (in repo)

---

## HTTPTrigger API

MiniTrini starts a local HTTP server on boot at `127.0.0.1:5005`.

### Endpoints

**GET /ping**
```bash
curl http://localhost:5005/ping
# {"status": "alive", "app": "MiniTrini", "port": 5005}
```

**POST /trigger**
```bash
curl -X POST http://localhost:5005/trigger \
  -H "Content-Type: application/json" \
  -d '{"message": "your message here", "agent": "Trini"}'
# {"status": "ok", "received": "your message here"}
```

Message is injected directly into `process_user_input` — same path as manual chat input. All governance rules, `@kg:`, and `@multi` intercepts apply.

Response is immediate (`200 OK`) — processing is async.

---

## Knowledge Graph

SQLite database at `~/.minitrini/knowledge_graph.db`.

**Schema:**
```sql
nodes (id, speaker, content, source, timestamp)
edges (id, from_id, to_id, relation)
```

- Every User and Assistant turn is logged as a node
- Sequential turns are linked by `follows` edges
- `source` field: `chat` | `canvas` | `multi_agent`

**Query:**
```
@kg: <keyword>
```
Searches `content` and `speaker` fields via SQL `LIKE`. Returns up to 20 most recent matches. Output to Canvas only.

**Direct DB access:**
```bash
python3 -c "
import sqlite3, os
con = sqlite3.connect(os.path.expanduser('~/.minitrini/knowledge_graph.db'))
cur = con.cursor()
cur.execute('SELECT speaker, content, timestamp FROM nodes ORDER BY id DESC LIMIT 10')
for r in cur.fetchall(): print(r)
con.close()
"
```

---

## Governance Reference

Rules file: `governance.yaml` (in repo, committed).
Ledger: `~/.minitrini/governance_ledger.jsonl` (outside repo).

**Actions:**

| Action | Behaviour |
|--------|-----------|
| `block` | Input rejected. System message displayed: `⚖ Governance block [rule_id]: description` |
| `confirm` | Execution paused. Amber input box shown with rule description. Proceeds only if V confirms. |

**Default rules:**

| ID | Triggers | Action |
|----|----------|--------|
| `no_destructive_commands` | `rm -rf`, `rmdir /s`, `format c:`, `wipe`, `dd if=/dev/zero` | block |
| `no_credential_exposure` | `api_key`, `secret_key`, `password=`, `token=`, `private_key` | block |
| `self_modification_confirm` | `self_patch`, `_rollback`, `overwrite minitrini_noi_pulse`, `replace minitrini_noi_pulse` | confirm |
| `no_external_exfiltration` | `curl http`, `wget http`, `requests.post('http`, `requests.get('http` | block |

---

## Key File Paths Reference

| Path | Purpose | In Repo |
|------|---------|---------|
| `minitrini_noi_pulse.py` | Main application | ✓ |
| `TrinityCanvas.py` | Canvas IDE | ✓ |
| `minitrini_guard.py` | Integrity guard | ✓ |
| `governance.yaml` | Governance rules | ✓ |
| `.minitrini_manifest.json` | Guard SHA-256 manifest | ✓ |
| `engine/agents.py` | Agent definitions | ✓ |
| `engine/tools.py` | Tool definitions | ✓ |
| `backend/router.py` | LLM router | ✓ |
| `plugins/` | Plugin directory | ✓ |
| `core/flows/` | Flow YAML files | ✓ |
| `~/.minitrini/knowledge_graph.db` | Knowledge graph | ✗ |
| `~/.minitrini/last_session.json` | Session memory | ✗ |
| `~/.minitrini/feedback_log.json` | Feedback log | ✗ |
| `~/.minitrini/snapshots/` | Snapshots directory | ✗ |
| `~/.minitrini/governance_ledger.jsonl` | Governance ledger | ✗ |
| `~/.minitrini/user_profile.json` | User profile | ✗ |
| `minitrini_env/` | Python venv | ✗ |

---

## Session Bootstrap Injection Order

On every boot, the following are injected into the LLM context in order:

1. `_kg_init()` — knowledge graph DB initialized
2. `_gov_load()` — governance rules loaded
3. `_load_session_memory()` — last 12 exchanges from previous session
4. `_load_feedback_tone()` — tone hints from feedback log
5. Session bootstrap constants — structure, mode, constraints

---

*MiniTrini v10.1 — Session 009 — 2026-04-27*
