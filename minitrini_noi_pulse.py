#!/usr/bin/env python3
# MiniTrini_v10.1 — Trinity Multi-Agent Edition with Pulse Glow + Training Engine


import time
import math
import tkinter as tk
from tkinter import ttk, scrolledtext
from tkinterdnd2 import TkinterDnD, DND_FILES
from datetime import datetime
import json, os, stat, requests
from pathlib import Path
import sys
import subprocess
import threading
from subprocess import PIPE
import re
import platform
import os
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_DATASETS_OFFLINE", "1")
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
from AI_Core.TrinityMemoryBank.trini_vector_memory import TriniVectorMemory
import inspect
from TrinityCanvas import open_canvas, send_to_canvas, create_module
from bs4 import BeautifulSoup
import json
from urllib.parse import quote
from engine.tools import TOOLS, run_tool_logic
from engine.plugin_loader import load_plugins, run_plugin, unload_plugin, list_plugins
from engine.agents import AGENTS
from engine.engine import MiniTriniEngine
from backend.router import BackendRouter
# Orchestration engine
import sys as _sys
_sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from core.orchestrator import Orchestrator
from core.flow_loader import load_flow
from core.context import Context
from core.triggers_manual import ManualTrigger
from core.backend_safety import detect_hardware, select_backend, safe_defaults
from collections import Counter

print("LOADED FROM:", inspect.getfile(TriniVectorMemory))
print("METHODS:", dir(TriniVectorMemory))


print(TriniVectorMemory)
print(dir(TriniVectorMemory))

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
# -----------------------------
#  BACKEND PROCESS (MAIN.PY)
# -----------------------------


# -----------------------------
#  LLAMA.CPP DETECTION
# -----------------------------
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except Exception:
    LLAMA_AVAILABLE = False


# -----------------------------
#  THEME CONSTANTS
# -----------------------------
ACCENT = "#b347ff"
GLOW1  = "#b347ff"
GLOW2  = "#33eaff"
BG_MAIN = "#0f0014"
BG_PANEL = "#1a001f"
BG_TEXTBOX = "#120016"
TEXT_SOFT = "#d28cff"

MODEL_DIR  = Path(__file__).resolve().parent / "AI_Core" / "Models"
RULES_FILE = Path("./AI_Core/TrinityMemoryBank/refusal_rules.json")



# ======================================================================
#  MINI TRINI APP — CLEAN, STRUCTURALLY RESTORED
# ======================================================================
class MiniTriniApp:


    REFINEMENT_DIRECTIVE = (
        "Refine the following text for clarity, structure, and coherence.\n"
        "Remove filler. Improve reasoning. Preserve intent.\n"
    )
    
    def emit(self, channel, sender, message):
        """
        channel = 'chat' or 'console'
        """

        if channel == "chat":
            formatted = f"{sender}: {message}\n"
            self.output_box.insert("end", formatted)
            self.output_box.see("end")

        elif channel == "console":
            timestamp = datetime.now().strftime("%H:%M:%S")
            line = f"[{timestamp}] [{sender}] {message}"
            self.console_print(line)    

    def log_executive_event(self, event_type, message):
        timestamp = datetime.now().strftime("%H:%M:%S")

        line = f"[{timestamp}] [{event_type}] {message}"
        self.console_print(line)

    def __init__(self, root):
        self.root = root
        root.title("🧠 MiniTrini v10.1 — Multi-Agent Trinity Console")
        root.configure(bg=BG_MAIN)
        root.geometry("1080x800")
        
        #self.vector_memory = TriniVectorMemory(Path(__file__).resolve().parent)   
        PROJECT_ROOT = Path(__file__).resolve().parent
        MEMORY_DIR = PROJECT_ROOT / "AI_Core" / "TrinityMemoryBank" / "trained_memory"
        from AI_Core.Executive.trini_executive import TriniExecutive
        self.executive = TriniExecutive(PROJECT_ROOT)
        self.backend_router = BackendRouter(self)
        
        

        self.vector_memory = TriniVectorMemory(MEMORY_DIR)        
                     
        active_goals = self.executive.get_active_goals()
        if active_goals:
            self.pipeline(f"Executive: {len(active_goals)} active goals detected.")


        # Backend state
        self.backend_mode = "local"
        self.llm = None
        self.llm_lock = __import__("threading").Lock()
        self.local_model_loaded = False
        
        system = platform.system()

        if system == "Darwin":
            self.speed_profile = "runtime"
        else:
            self.speed_profile = "build"  
                  
        print(f"[MiniTrini] Detected OS: {system} | Profile: {self.speed_profile}")

        # Runtime state stores
        self.memory = []
        self.active_agent = AGENTS[0]
        self.active_tool  = None
        self.memory_log   = []
        self._canvas_context = {}
        self._local_calls = 0
        self._external_calls = 0
        self._local_agents = set()
        self._external_agents = set()
        self._pause_event = None
        self._pause_question = None

        
        self.init_state_engine()
        self.state["memory_items"] = 0
        self.state["tokens"] = 0
        self.state["pipeline"] = []

        self.state_set_agent(self.active_agent["name"])

        self.backend_process = None
        self.core_runtime_window = None

        self._load_user_profile()
        self._plugin_count = load_plugins(TOOLS)
        print(f'[MiniTrini] {self._plugin_count} plugin(s) loaded.')
        self.build_ui()
        self.build_agents_panel()
        self.build_tools_panel()

        self.open_agents_panel()
        self.open_tools_panel()
        self.speed_profile = "build"  # default
        
        self.console_window = None
        self.console_box = None        

        # --- SARA Mode State ---
        self.sara_mode = False          # User toggle (persistent)
        self.sara_autopilot = False     # Auto-activated (one-response)
        
        # ===== Developer Menu =====
        menubar = tk.Menu(self.root)

        dev_menu = tk.Menu(menubar, tearoff=0)
        dev_menu.add_command(label="State Monitor", command=self.toggle_devtools)
        dev_menu.add_command(label="Console", command=self.open_console_devtools)
        dev_menu.add_command(label="Training Panel", command=self.open_training_panel)
        dev_menu.add_command(label="Toggle DevTools", command=self.toggle_devtools)
        dev_menu.add_command(label="Goal Dashboard", command=self.open_goal_dashboard)
        # Attach menu to the window
        menubar.add_cascade(label="Developer", menu=dev_menu)
        self.root.config(menu=menubar)

        # ── VIVARIUM boot ping — non-blocking ─────────────────
        import threading as _bt
        def _boot_ping():
            self._shared_state_init()
            self._ethica_ping()
        _bt.Thread(target=_boot_ping, daemon=True).start()
        # ─────────────────────────────────────────────────────

    def open_goal_dashboard(self):

        if hasattr(self, "goal_win") and self.goal_win.winfo_exists():
            self.goal_win.lift()
            return

        self.goal_win = tk.Toplevel(self.root)
        self.goal_win.title("Executive Goal Dashboard")
        self.goal_win.geometry("600x400")
        self.goal_win.configure(bg=BG_PANEL)

        self.goal_text = tk.Text(
            self.goal_win,
            bg=BG_TEXTBOX,
            fg=ACCENT,
            font=("JetBrains Mono", 11)
        )
        self.goal_text.pack(fill="both", expand=True, padx=10, pady=10)

        btn_frame = tk.Frame(self.goal_win, bg=BG_PANEL)
        btn_frame.pack(fill="x", padx=10, pady=(0, 8))

        tk.Button(
            btn_frame,
            text="⟳ Refresh",
            command=self.refresh_goal_dashboard,
            bg=BG_TEXTBOX,
            fg=ACCENT,
            font=("JetBrains Mono", 10, "bold"),
            relief="ridge"
        ).pack(side="left", padx=4)

        def clear_completed():
            self.executive.goals = [g for g in self.executive.goals if g["status"] != "complete"]
            self.executive._save()
            self.refresh_goal_dashboard()

        tk.Button(
            btn_frame,
            text="🗑 Clear Completed",
            command=clear_completed,
            bg="#3a003a",
            fg="#c586c0",
            font=("JetBrains Mono", 10, "bold"),
            relief="ridge"
        ).pack(side="left", padx=4)

        def _auto_refresh():
            if hasattr(self, "goal_win") and self.goal_win.winfo_exists():
                self.refresh_goal_dashboard()
                self.goal_win.after(5000, _auto_refresh)

        self.goal_win.after(5000, _auto_refresh)
        self.refresh_goal_dashboard()
        self.log_executive_event(
            "SUMMARY",
            f"Completed Tasks: {len([g for g in self.executive.goals if g['status'] == 'complete'])}"
        )    

    def refresh_goal_dashboard(self):

        # Reload from disk (single source of truth)
        self.executive.goals = self.executive._load()
        goals = self.executive.goals

        self.goal_text.delete("1.0", "end")

        for g in goals:
            block = f"""
    ID: {g['id']}
    Objective: {g['objective']}
    Status: {g['status']}
    Priority: {g.get('priority')}
    Cycles: {g.get('cycle_count', 0)}
    Last Update: {g['last_update']}
    ------------------------------
    """
            self.goal_text.insert("end", block)

    def open_console_devtools(self):
        # If console is already open, lift it
        if hasattr(self, "console_win") and self.console_win.winfo_exists():
            self.console_win.lift()
            return

        # Create Console DevTools Window
        self.console_win = tk.Toplevel(self.root)
        self.console_win.title("Console DevTools")
        self.console_win.geometry("700x500")
        self.console_win.configure(bg=BG_PANEL)

        # Text area for log display
        self.console_output = scrolledtext.ScrolledText(
            self.console_win,
            wrap="word",
            bg=BG_TEXTBOX,
            fg=ACCENT,
            font=("JetBrains Mono", 11),
            relief="groove",
            insertbackground="white"
        )
        self.console_output.pack(fill="both", expand=True, padx=10, pady=10)

        # Initial message
        self.console_output.insert("end", "[Console] DevTools Console Initialized.\n")
        self.console_output.see("end")
        
    def console_print(self, text):
        if hasattr(self, "console_output"):
            try:
                self.console_output.insert("end", text + "\n")
                self.console_output.see("end")
            except:
                pass        

    def toggle_devtools(self):
        if self.devtools_active:
            self.close_devtools()
        else:
            self.open_devtools()

    def process_training_pass(self, text):
        prompt = (
            self.REFINEMENT_DIRECTIVE
            + "\n\n---\nTEXT:\n"
            + text
            + "\n---\nREFINED:\n"
        )

        result = self.backend_router.send(prompt)
        return result.strip()
        print("\n===== FINAL PROMPT SENT TO MODEL =====\n")
        print(prompt)
        print("\n=======================================\n")
        
        

    def state_set_task(self, task):
        self.state["task"] = task
        self.state["status"] = "Running"
        self.update_devtools()


    def display_message(self, sender, message):
        """
        Unified output renderer for MiniTrini v10.1
        Displays assistant or system messages in the main output box.
        """
        if not message:
            return

        formatted = f"{sender}: {message}\n"
        self.output_box.insert("end", formatted)
        self.output_box.see("end")
        
    

    def close_core_runtime(self):
        if self.backend_process:
            try:
                # Attempt graceful shutdown
                self.backend_process.terminate()
                self.backend_process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                # Force kill if it refuses to die
                self.backend_process.kill()
            except Exception:
                pass
            finally:
                self.backend_process = None

        if self.core_runtime_window:
            try:
                self.core_runtime_window.destroy()
            except:
                pass
            self.core_runtime_window = None
            self.core_runtime_active = False       
            
    def _get_generation_config(self):
        if self.speed_profile == "build":
            return {
                "max_tokens": 160,
                "temperature": 0.3,
            }
        elif self.speed_profile == "runtime":
            return {
                "max_tokens": 256,
                "temperature": 0.7,
            }                

    def _toggle_speed_profile(self):
        if self.speed_profile == "build":
            self.speed_profile = "runtime"
            self.profile_button.config(text="Profile: RUNTIME")
        else:
            self.speed_profile = "build"
            self.profile_button.config(text="Profile: BUILD")
            
    def save_trained_memory(self, content):
        trained_dir = Path(__file__).resolve().parent / "AI_Core" / "TrinityMemoryBank" / "trained_memory"
        trained_dir.mkdir(parents=True, exist_ok=True)

        filename = f"trained_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        path = trained_dir / filename

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

        return path            

    # --- User Identity System ---

    def _load_user_profile(self):
        import json, os
        profile_path = os.path.expanduser("~/.minitrini/user_profile.json")
        if os.path.exists(profile_path):
            try:
                with open(profile_path, "r") as f:
                    self._user_profile = json.load(f)
                print(f"[MiniTrini] User profile loaded: {self._user_profile.get('name', 'Unknown')}")
                return
            except Exception as e:
                print(f"[MiniTrini] Profile load error: {e}")
        self._user_profile = {}

    def _seal_guard(self):
        """Run minitrini_guard.py heal then seal from inside the UI."""
        import subprocess, os, pathlib
        guard = str(pathlib.Path(__file__).resolve().parent / "minitrini_guard.py")
        python = str(pathlib.Path(__file__).resolve().parent / "minitrini_env" / "bin" / "python3")
        def _run():
            for cmd in ["heal", "seal"]:
                result = subprocess.run(
                    [python, guard, cmd],
                    capture_output=True, text=True
                )
                out = result.stdout.strip() or result.stderr.strip()
                self.root.after(0, lambda msg=out: self.pipeline(f"Guard: {msg}"))
                self.root.after(0, lambda msg=out: self.emit("chat", "System", msg))
        import threading
        threading.Thread(target=_run, daemon=True).start()

    def _snapshot(self):
        """Snapshot minitrini_noi_pulse.py to ~/.minitrini/snapshots/ before any self-patch."""
        import shutil, os
        from datetime import datetime
        snap_dir = os.path.expanduser("~/.minitrini/snapshots")
        os.makedirs(snap_dir, exist_ok=True)
        src_path = os.path.abspath(__file__)
        ts = datetime.utcnow().strftime("%Y%m%dT%H%M%SZ")
        dst = os.path.join(snap_dir, f"minitrini_noi_pulse_{ts}.py")
        shutil.copy2(src_path, dst)
        snaps = sorted(os.listdir(snap_dir))
        for old in snaps[:-10]:
            os.remove(os.path.join(snap_dir, old))
        self.pipeline(f"Trini: Snapshot saved → {os.path.basename(dst)}")
        return dst

    def _rollback(self):
        """Restore the most recent snapshot of minitrini_noi_pulse.py."""
        import shutil, os
        snap_dir = os.path.expanduser("~/.minitrini/snapshots")
        if not os.path.exists(snap_dir):
            self.emit("chat", "System", "No snapshots found.")
            return
        snaps = sorted([f for f in os.listdir(snap_dir) if f.startswith("minitrini_noi_pulse_")])
        if not snaps:
            self.emit("chat", "System", "No snapshots available to restore.")
            return
        latest = os.path.join(snap_dir, snaps[-1])
        dst = os.path.abspath(__file__)
        # Auto-snapshot current state before overwriting
        self._snapshot()
        shutil.copy2(latest, dst)
        self.emit("chat", "System", f"Rolled back to {snaps[-1]} — restart to apply.")
        self.pipeline(f"Trini: Rollback applied → {snaps[-1]}")

    def _save_feedback(self, rating, message_snippet):
        """Append a feedback entry to ~/.minitrini/feedback_log.json."""
        import json, os
        from datetime import datetime
        path = os.path.expanduser("~/.minitrini/feedback_log.json")
        try:
            with open(path, "r") as f:
                log = json.load(f)
        except Exception:
            log = []
        log.append({
            "timestamp": datetime.utcnow().isoformat(),
            "rating": rating,
            "snippet": message_snippet[:120]
        })
        # Keep last 200 entries
        log = log[-200:]
        with open(path, "w") as f:
            json.dump(log, f, indent=2)
        self.pipeline(f"Trini: Feedback recorded — {rating}")

    def _insert_feedback_buttons(self, response_text):
        """Embed 👍 👎 buttons inline after assistant message."""
        snippet = response_text.strip()[:120]

        def on_good():
            self._save_feedback("thumbs_up", snippet)
            btn_good.config(state="disabled")
            btn_bad.config(state="disabled")

        def on_bad():
            self._save_feedback("thumbs_down", snippet)
            btn_good.config(state="disabled")
            btn_bad.config(state="disabled")

        self.output_box.insert("end", "  ")
        btn_good = tk.Button(
            self.output_box,
            text="👍", command=on_good,
            bg="#1e1e2e", fg="#4ec94e",
            font=("JetBrains Mono", 10),
            relief="flat", padx=4, pady=0,
            cursor="hand2"
        )
        self.output_box.window_create("end", window=btn_good)
        self.output_box.insert("end", " ")
        btn_bad = tk.Button(
            self.output_box,
            text="👎", command=on_bad,
            bg="#1e1e2e", fg="#ff4444",
            font=("JetBrains Mono", 10),
            relief="flat", padx=4, pady=0,
            cursor="hand2"
        )
        self.output_box.window_create("end", window=btn_bad)
        self.output_box.insert("end", "\n")
        self.output_box.see("end")

    def _load_feedback_tone(self):
        """Derive tone hints from last 20 feedback entries."""
        import json, os
        path = os.path.expanduser("~/.minitrini/feedback_log.json")
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "r") as f:
                log = json.load(f)
            recent = log[-20:]
            ups = sum(1 for e in recent if e.get("rating") == "thumbs_up")
            downs = sum(1 for e in recent if e.get("rating") == "thumbs_down")
            if not recent:
                return ""
            hints = ["[FeedbackTone]"]
            if downs > ups:
                hints.append("• Recent feedback signals: be more concise, reduce verbosity")
            elif ups > downs:
                hints.append("• Recent feedback signals: tone is working well, maintain warmth")
            else:
                hints.append("• Feedback balanced — maintain current tone")
            hints.append("")
            return "\n".join(hints) + "\n"
        except Exception:
            return ""




    def _http_trigger_start(self, port=5005):
        """Start lightweight HTTP server — MiniTrini callable by Ethica/TrinityBrowseSe."""
        from http.server import HTTPServer, BaseHTTPRequestHandler
        import json, threading

        app_ref = self

        class TriggerHandler(BaseHTTPRequestHandler):
            def log_message(self, format, *args):
                pass  # silence request logs

            def do_POST(self):
                if self.path != "/trigger":
                    self.send_response(404)
                    self.end_headers()
                    return
                try:
                    length = int(self.headers.get("Content-Length", 0))
                    body = self.rfile.read(length)
                    data = json.loads(body)
                    message = data.get("message", "").strip()
                    if message:
                        app_ref.root.after(0, lambda m=message: app_ref.process_user_input(m))
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "ok", "received": message}).encode())
                except Exception as e:
                    self.send_response(500)
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "error", "detail": str(e)}).encode())

            def do_GET(self):
                if self.path == "/ping":
                    self.send_response(200)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(json.dumps({"status": "alive", "app": "MiniTrini", "port": port}).encode())
                else:
                    self.send_response(404)
                    self.end_headers()

        def _serve():
            try:
                server = HTTPServer(("127.0.0.1", port), TriggerHandler)
                app_ref.root.after(0, lambda: app_ref.pipeline(f"⟁ HTTPTrigger live — localhost:{port}/trigger"))
                server.serve_forever()
            except OSError as e:
                app_ref.root.after(0, lambda: app_ref.pipeline(f"⚠ HTTPTrigger failed to bind port {port}: {e}"))

        threading.Thread(target=_serve, daemon=True).start()

    def _shared_state_init(self):
        import os, json
        state_dir = os.path.expanduser("~/.trinity")
        os.makedirs(state_dir, exist_ok=True)
        state_path = os.path.join(state_dir, "shared_state.json")
        if not os.path.exists(state_path):
            with open(state_path, "w") as f:
                json.dump({}, f, indent=2)

    def _shared_state_write(self, key, value):
        import os, json
        state_path = os.path.expanduser("~/.trinity/shared_state.json")
        try:
            with open(state_path, "r") as f:
                state = json.load(f)
        except Exception:
            state = {}
        state[key] = value
        tmp = state_path + ".tmp"
        with open(tmp, "w") as f:
            json.dump(state, f, indent=2)
        os.replace(tmp, state_path)

    def _shared_state_read(self, key=None):
        import json, os
        state_path = os.path.expanduser("~/.trinity/shared_state.json")
        try:
            with open(state_path, "r") as f:
                state = json.load(f)
            return state.get(key) if key else state
        except Exception:
            return None if key else {}

    def _gov_load(self):
        """Load governance rules from governance.yaml."""
        import yaml, os
        gov_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "governance.yaml")
        try:
            with open(gov_path, "r") as f:
                data = yaml.safe_load(f)
            self._gov_rules = data.get("rules", [])
        except Exception as e:
            self._gov_rules = []
            print(f"[GOV] Failed to load governance.yaml: {e}")

    def _gov_check(self, text):
        """Check input against governance rules. Returns (action, rule) or (None, None)."""
        tl = text.lower()
        for rule in getattr(self, "_gov_rules", []):
            for trigger in rule.get("triggers", []):
                if trigger.lower() in tl:
                    return rule.get("action"), rule
        return None, None

    def _gov_log(self, text, rule, action):
        """Append governance event to ledger."""
        import json, os
        from datetime import datetime
        ledger = os.path.expanduser("~/.minitrini/governance_ledger.jsonl")
        os.makedirs(os.path.dirname(ledger), exist_ok=True)
        entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "rule_id": rule.get("id"),
            "description": rule.get("description"),
            "input_snippet": text[:120]
        }
        with open(ledger, "a") as f:
            f.write(json.dumps(entry) + "\n")

    def _kg_init(self):
        """Initialize local knowledge graph SQLite DB."""
        import sqlite3, os
        db_path = os.path.expanduser("~/.minitrini/knowledge_graph.db")
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        con = sqlite3.connect(db_path)
        cur = con.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS nodes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                speaker TEXT,
                content TEXT,
                source TEXT DEFAULT 'chat',
                timestamp TEXT
            )
        """)
        cur.execute("""
            CREATE TABLE IF NOT EXISTS edges (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_id INTEGER,
                to_id INTEGER,
                relation TEXT DEFAULT 'follows'
            )
        """)
        con.commit()
        con.close()

    def _kg_add_turn(self, speaker, content, source="chat"):
        """Add a conversation turn as a node, edge to previous."""
        import sqlite3, os
        from datetime import datetime
        db_path = os.path.expanduser("~/.minitrini/knowledge_graph.db")
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            cur.execute(
                "INSERT INTO nodes (speaker, content, source, timestamp) VALUES (?, ?, ?, ?)",
                (speaker, content, source, datetime.utcnow().isoformat())
            )
            new_id = cur.lastrowid
            cur.execute("SELECT MAX(id) FROM nodes WHERE id < ?", (new_id,))
            prev = cur.fetchone()[0]
            if prev:
                cur.execute(
                    "INSERT INTO edges (from_id, to_id, relation) VALUES (?, ?, ?)",
                    (prev, new_id, "follows")
                )
            con.commit()
            con.close()
        except Exception as e:
            print(f"[KG] add_turn error: {e}")

    def _kg_query(self, query):
        """Keyword search over knowledge graph nodes. Output to canvas."""
        import sqlite3, os
        db_path = os.path.expanduser("~/.minitrini/knowledge_graph.db")
        try:
            con = sqlite3.connect(db_path)
            cur = con.cursor()
            like = f"%{query}%"
            cur.execute(
                "SELECT speaker, content, source, timestamp FROM nodes WHERE content LIKE ? OR speaker LIKE ? ORDER BY id DESC LIMIT 20",
                (like, like)
            )
            rows = cur.fetchall()
            con.close()
            if not rows:
                result = (
                    f"# ⟁ Knowledge Graph\n"
                    f"**Query:** `{query}`\n\n"
                    f"_No matching records found in the knowledge graph._"
                )
            else:
                lines = [
                    f"# ⟁ Knowledge Graph",
                    f"**Query:** `{query}` — **{len(rows)} result(s)**\n",
                ]
                for speaker, content, source, ts in rows:
                    try:
                        from datetime import datetime
                        ts_clean = datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        ts_clean = ts
                    preview = content.strip()[:300] + ("..." if len(content.strip()) > 300 else "")
                    lines.append(
                        f"---\n"
                        f"🕐 `{ts_clean}` &nbsp;|&nbsp; 🗣 **{speaker}** &nbsp;|&nbsp; 📂 _{source}_\n\n"
                        f"{preview}\n"
                    )
                result = "\n".join(lines)
            send_to_canvas(result)
        except Exception as e:
            send_to_canvas(f"# KG Error\n{e}")

    def _save_session_memory(self):
        """Save last session memory to ~/.minitrini/last_session.json on close."""
        import json, os
        if not self.memory:
            return
        profile_dir = os.path.expanduser("~/.minitrini")
        os.makedirs(profile_dir, exist_ok=True)
        path = os.path.join(profile_dir, "last_session.json")
        entries = [{"role": r, "text": t} for r, t in self.memory[-40:]]
        with open(path, "w") as f:
            json.dump({"turns": entries}, f, indent=2)
        print(f"[MiniTrini] Session memory saved ({len(entries)} turns).")

    def _load_session_memory(self):
        """Load last session summary string for bootstrap injection."""
        import json, os
        path = os.path.expanduser("~/.minitrini/last_session.json")
        if not os.path.exists(path):
            return ""
        try:
            with open(path, "r") as f:
                data = json.load(f)
            turns = data.get("turns", [])
            if not turns:
                return ""
            # Build compact replay — last 6 exchanges max
            lines = ["[MemoryReplay — last session]"]
            for t in turns[-12:]:
                role = t.get("role", "?")
                text = t.get("text", "").strip().replace("\n", " ")
                lines.append(f"• {role}: {text[:120]}")
            lines.append("")
            return "\n".join(lines) + "\n"
        except Exception as e:
            print(f"[MiniTrini] Memory replay load failed: {e}")
            return ""

        self.root.after(500, self._run_setup_wizard)

    def _run_setup_wizard(self):
        import json, os, tkinter as tk
        from tkinter import simpledialog, messagebox
        messagebox.showinfo(
            "Welcome to MiniTrini",
            "Trini would like to know who she is working with.\n\nA quick setup — just a few questions."
        )
        name = simpledialog.askstring("Your Name", "What is your name?", parent=self.root)
        if not name:
            name = "Architect"
        address = simpledialog.askstring(
            "Preferred Address",
            f"How should Trini address you?\n(e.g. V, Victory, Boss — default: {name})",
            parent=self.root
        )
        if not address:
            address = name
        project = simpledialog.askstring(
            "Current Project",
            "What are you currently building or working on?",
            parent=self.root
        )
        if not project:
            project = "a sovereign AI platform"
        style = simpledialog.askstring(
            "Communication Style",
            "How should Trini communicate with you?\n(e.g. direct, warm, technical, casual)",
            parent=self.root
        )
        if not style:
            style = "direct and warm"
        profile = {
            "name": name,
            "address": address,
            "project": project,
            "style": style
        }
        profile_dir = os.path.expanduser("~/.minitrini")
        os.makedirs(profile_dir, exist_ok=True)
        profile_path = os.path.join(profile_dir, "user_profile.json")
        with open(profile_path, "w") as f:
            json.dump(profile, f, indent=2)
        self._user_profile = profile
        self.pipeline(f"Trini: Welcome, {address}. Profile saved. I won\'t forget you.")
        print(f"[MiniTrini] Profile created: {profile_path}")

    def _open_profile_editor(self):
        import json, os, tkinter as tk
        win = tk.Toplevel(self.root)
        win.title("Edit User Profile")
        win.configure(bg="#1a1a2e")
        win.geometry("420x320")
        fields = ["name", "address", "project", "style"]
        labels = ["Your Name", "Preferred Address", "Current Project", "Communication Style"]
        entries = {}
        for i, (field, label) in enumerate(zip(fields, labels)):
            tk.Label(win, text=label, bg="#1a1a2e", fg="#a0c4ff", font=("Courier", 11)).grid(
                row=i, column=0, sticky="w", padx=16, pady=8)
            e = tk.Entry(win, bg="#0d0d1a", fg="#e0e0e0", font=("Courier", 11), width=28,
                        insertbackground="white")
            e.insert(0, self._user_profile.get(field, ""))
            e.grid(row=i, column=1, padx=8, pady=8)
            entries[field] = e

        def save():
            for field in fields:
                self._user_profile[field] = entries[field].get().strip()
            profile_path = os.path.expanduser("~/.minitrini/user_profile.json")
            with open(profile_path, "w") as f:
                json.dump(self._user_profile, f, indent=2)
            self.pipeline(f"Trini: Profile updated. Hello, {self._user_profile.get('address', 'Architect')}.")
            # ── Write soulprint to CMA/CAI soul files ─────────────
            import datetime
            user_name = self._user_profile.get("name", "").strip()
            if user_name:
                soulprint_id = f"{user_name}-001"
                import pathlib as _pl, json as _json
                _tb = _pl.Path(__file__).resolve().parent / "AI_Core" / "TrinityMemoryBank"
                anchor_path = _tb / "session_anchor.json"
                soulmark_path = _tb / "SoulMarkSignature.key"
                seed_path = _tb / "Trinity_Seed_Scroll.json"
                try:
                    anchor = {"status": "initialized", "started": datetime.datetime.utcnow().isoformat() + "Z", "soulprint": soulprint_id}
                    anchor_path.write_text(_json.dumps(anchor, indent=2))
                    soulmark_path.write_text(f"SOULMARK::{soulprint_id}::signed")
                    seed = _json.loads(seed_path.read_text()) if seed_path.exists() else {}
                    seed["soulprint"] = soulprint_id
                    seed_path.write_text(_json.dumps(seed, indent=2))
                    print(f"[MiniTrini] Soulprint updated → {soulprint_id}", flush=True)
                except Exception as e:
                    print(f"[MiniTrini] Soulprint write failed: {e}", flush=True)
            win.destroy()

        tk.Button(win, text="Save Profile", command=save,
                  bg="#2a2a4a", fg="#a0c4ff", font=("Courier", 11),
                  relief="flat", padx=12, pady=6).grid(
                  row=len(fields), column=0, columnspan=2, pady=16)

    # --- End User Identity System ---

    # --- Plugin Manager ---

    def _open_plugin_manager(self):
        import tkinter as tk
        import shutil
        from pathlib import Path
        if hasattr(self, '_plugin_manager_win') and self._plugin_manager_win.winfo_exists():
            self._plugin_manager_win.lift()
            return

        win = tk.Toplevel(self.root)
        self._plugin_manager_win = win
        win.title("Plugin Manager")
        win.configure(bg="#1a1a2e")
        win.geometry("480x400")

        tk.Label(win, text="👾 Installed Plugins", bg="#1a1a2e", fg="#c084fc",
                 font=("Courier", 13, "bold")).pack(pady=10)

        list_frame = tk.Frame(win, bg="#1a1a2e")
        list_frame.pack(fill="both", expand=True, padx=16)

        def refresh():
            for w in list_frame.winfo_children():
                w.destroy()
            plugin_tools = [t for t in TOOLS if t.get("plugin")]
            if not plugin_tools:
                tk.Label(list_frame, text="No plugins installed.", bg="#1a1a2e",
                         fg="#666", font=("Courier", 11)).pack(pady=20)
                return
            for t in plugin_tools:
                row = tk.Frame(list_frame, bg="#0d0d1a", pady=4)
                row.pack(fill="x", pady=3)
                tk.Label(row, text=f"{t['icon']}  {t['name']}",
                         bg="#0d0d1a", fg="#e0e0e0",
                         font=("Courier", 11), width=28, anchor="w").pack(side="left", padx=8)
                def make_delete(tool=t):
                    def delete():
                        plugin_dir = Path(tool.get("plugin_dir", ""))
                        if plugin_dir.exists():
                            shutil.rmtree(plugin_dir)
                        unload_plugin(tool["intent"], TOOLS)
                        self.pipeline(f"Trini: Plugin '{tool['name']}' removed.")
                        refresh()
                        # Rebuild tools panel
                        try:
                            self.tools_win.destroy()
                        except:
                            pass
                        self.build_tools_panel()
                    return delete
                tk.Button(row, text="🗑 Delete", command=make_delete(),
                          bg="#3a0a0a", fg="#ff6b6b",
                          font=("Courier", 10), relief="flat", padx=8).pack(side="right", padx=8)

        refresh()

        # Reload button
        def reload_all():
            count = load_plugins(TOOLS)
            self.pipeline(f"Trini: Plugin registry reloaded — {count} new plugin(s) found.")
            refresh()
            try:
                self.tools_win.destroy()
            except:
                pass
            self.build_tools_panel()

        tk.Button(win, text="🔄 Reload Registry", command=reload_all,
                  bg="#1e1e2e", fg="#c084fc", font=("Courier", 11),
                  relief="flat", padx=12, pady=6).pack(pady=12)

    # --- End Plugin Manager ---

    def _launch_vivarium_dashboard(self):
        """Launch the VIVARIUM dashboard — standalone Tkinter process."""
        import subprocess, pathlib
        dashboard = pathlib.Path.home() / ".trinity" / "vivarium_dashboard.py"
        if not dashboard.exists():
            import tkinter.messagebox as mb
            mb.showerror("VIVARIUM", f"Dashboard not found at {dashboard}")
            return
        subprocess.Popen(
            ["python3", str(dashboard)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

    def _ethica_ping(self):
        """Ping Ethica HTTP trigger on boot — write result to shared_state."""
        import urllib.request, json, datetime
        try:
            req = urllib.request.urlopen("http://127.0.0.1:5006/ping", timeout=2)
            data = json.loads(req.read().decode())
            status = data.get("status", "unknown")
        except Exception:
            status = "offline"
        self._shared_state_write("ethica", {
            "status": status,
            "port": 5006,
            "checked": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        label = "🟢 Ethica LIVE" if status == "alive" else "⚪ Ethica offline"
        print(f"[MiniTrini] VIVARIUM bridge — {label}", flush=True)
        return status

    def build_session_bootstrap(self):
        self._kg_init()
        self._shared_state_init()
        self._ethica_ping()
        self._gov_load()
        replay = self._load_session_memory()
        tone = self._load_feedback_tone()
        return (
            replay +
            tone +
            "[SessionBootstrap]\n"
            "• Structure = stable\n"
            "• Tone = consistent\n"
            "• Mode = co-creative\n"
            "• Constraints = no drift, no flattening, be clear\n"
            "• Behavior = focused, concise, aligned\n\n"
        )

    def open_console(self):
        # If window already exists, lift it
        if self.console_window and self.console_window.winfo_exists():
            self.console_window.lift()
            return

        # Create window
        self.console_window = tk.Toplevel(self.root)
        self.console_window.title("MiniTrini Console")
        self.console_window.configure(bg="#150015")
        self.console_window.geometry("600x350+200+200")

        # Scrolled text box
        self.console_box = scrolledtext.ScrolledText(
            self.console_window,
            bg="black",
            fg="#00ff00",
            font=("JetBrains Mono", 10),
            insertbackground="white"
        )
        self.console_box.pack(fill="both", expand=True, padx=10, pady=10)

        # Initial message
        self.console_box.insert("end", "[Console Initialized]\n")
        self.console_box.see("end")
 
    def console_log(self, message):
        if self.console_box and self.console_box.winfo_exists():
            try:
                self.console_box.insert("end", message + "\n")
                self.console_box.see("end")
            except:
                pass
                         
    # ==================================================================
    #  UI BUILD
    # ==================================================================
    def build_ui(self):
        header = tk.Frame(self.root, bg=BG_MAIN)
        header.pack(fill="x", pady=8)

        tk.Label(
            header,
            text="🧠 MiniTrini v10.1 — ",
            fg=ACCENT,
            bg=BG_MAIN,
            font=("JetBrains Mono", 22, "bold")
        ).pack(side="left", padx=12)

        self.header_title = tk.Label(
            header,
            text="Multi-Agent Trinity Console",
            bg=BG_MAIN,
            fg=TEXT_SOFT,
            font=("JetBrains Mono", 18, "bold")
        )
        self.header_title.pack(side="left", padx=10)

        tk.Button(
            header,
            text="🧠 Core Runtime",
            bg=ACCENT,
            fg="black",
            font=("JetBrains Mono", 11, "bold"),
            relief="ridge",
            command=self.toggle_core_runtime
        ).pack(side="right", padx=12)

        # Chat window
        self.output_box = tk.Text(
            self.root,
            height=22,
            bg=BG_TEXTBOX,
            fg=ACCENT,
            font=("JetBrains Mono", 12),
            wrap="word",
            relief="groove",
            insertbackground="white",
        )
        self.output_box.pack(fill="both", expand=True, padx=20, pady=10)

        # Input bar
        input_frame = tk.Frame(self.root, bg=BG_MAIN)
        input_frame.pack(fill="x", padx=20, pady=5)

        self.input_box = tk.Entry(
            input_frame,
            bg=BG_TEXTBOX,
            fg=TEXT_SOFT,
            font=("JetBrains Mono", 12),
            insertbackground="white",
        )
        self.input_box.pack(side="left", fill="x", expand=True)
        self.input_box.bind("<Return>", self.send_message)

        self.send_btn = tk.Button(
            input_frame,
            text="Send",
            bg=ACCENT,
            fg="black",
            font=("JetBrains Mono", 11, "bold"),
            command=self.send_message
        )
        self.send_btn.pack(side="left", padx=10)

        _toolbar = tk.Frame(self.root, bg=BG_MAIN)
        _toolbar.pack(pady=4)
        self.profile_button = tk.Button(
            _toolbar,
            text="Profile: BUILD",
            bg=ACCENT,
            fg="black",
            command=self._toggle_speed_profile
        )
        self.profile_button.pack(side="left", padx=4)
        tk.Button(
            _toolbar,
            text="👤 Edit Profile",
            bg="#1e1e1e",
            fg="#a0c4ff",
            command=self._open_profile_editor
        ).pack(side="left", padx=4)
        tk.Button(
            _toolbar,
            text="👾 Plugins",
            bg="#1e1e1e",
            fg="#c084fc",
            command=self._open_plugin_manager
        ).pack(side="left", padx=4)
        tk.Button(
            _toolbar,
            text="⏪ Rollback",
            bg="#1e1e1e",
            fg="#f0a500",
            command=self._rollback
        ).pack(side="left", padx=4)
        tk.Button(
            _toolbar,
            text="🔒 Seal Guard",
            bg="#1e1e1e",
            fg="#c084fc",
            command=self._seal_guard
        ).pack(side="left", padx=4)
        tk.Button(
            _toolbar,
            text="🖼 Canvas",
            bg="#1e1e1e",
            fg="#569cd6",
            command=lambda: open_canvas(self)
        ).pack(side="left", padx=4)
        self.run_flow_btn = tk.Button(
            _toolbar,
            text="⟁ Run Flow",
            bg="#2a004a",
            fg=ACCENT,
            font=("JetBrains Mono", 10, "bold"),
            relief="ridge",
            command=self._run_orchestrator_flow
        )
        self.run_flow_btn.pack(side="left", padx=4)
        tk.Button(
            _toolbar,
            text="⟁ VIVARIUM",
            bg="#001a0e",
            fg="#00ff88",
            font=("JetBrains Mono", 10, "bold"),
            relief="ridge",
            command=self._launch_vivarium_dashboard
        ).pack(side="left", padx=4)


        self.drop_zone = tk.Label(
            self.root,
            text="Drop files here for Trinity",
            bg="#1e1e1e",
            fg="#c586c0",
            relief="ridge",
            height=3
        )
        self.drop_zone.pack(fill="x", padx=10, pady=5)
        self.drop_zone.drop_target_register(DND_FILES)
        self.drop_zone.dnd_bind("<<Drop>>", self.handle_file_drop)
        # --- Canvas Context Panel ---
        self.canvas_ctx_frame = tk.Frame(self.root, bg="#0d0d1a", relief="ridge", bd=1)
        self.canvas_ctx_frame.pack(fill="x", padx=10, pady=(2, 0))
        tk.Label(
            self.canvas_ctx_frame,
            text="Canvas Context",
            bg="#0d0d1a",
            fg="#569cd6",
            font=("JetBrains Mono", 9, "bold"),
            anchor="w"
        ).pack(fill="x", padx=6, pady=(4, 0))
        self.canvas_ctx_label = tk.Label(
            self.canvas_ctx_frame,
            text="— empty —",
            bg="#0d0d1a",
            fg="#808080",
            font=("JetBrains Mono", 8),
            anchor="w",
            justify="left",
            wraplength=340
        )
        self.canvas_ctx_label.pack(fill="x", padx=6, pady=(2, 2))
        tk.Button(
            self.canvas_ctx_frame,
            text="Clear Canvas Context",
            bg="#1e1e1e",
            fg="#c586c0",
            font=("JetBrains Mono", 8),
            relief="flat",
            command=self._clear_canvas_context
        ).pack(anchor="e", padx=6, pady=(0, 4))
        # --- End Canvas Context Panel ---
        tk.Label(
            self.root,
            text="Flow Prompt",
            bg="#0d0d1a",
            fg="#569cd6",
            font=("JetBrains Mono", 9, "bold"),
            anchor="w"
        ).pack(fill="x", padx=10, pady=(4, 0))
        self.flow_prompt_entry = tk.Entry(
            self.root,
            bg="#1e1e1e",
            fg="#c586c0",
            insertbackground="#c586c0",
            font=("JetBrains Mono", 9),
            relief="ridge"
        )
        self.flow_prompt_entry.insert(0, "Introduce yourself in one sentence.")
        self.flow_prompt_entry.pack(fill="x", padx=10, pady=(2, 2))


    # ==================================================================
    #  MESSAGE PIPELINE (NO DRIFT)
    # ==================================================================
    def _multi_agent_run(self, user_text):
        """Decompose task, run subtasks in parallel via ThreadPoolExecutor, synthesize."""
        import threading, json, re
        from concurrent.futures import ThreadPoolExecutor, as_completed
        from engine.agents import AGENTS

        def _run():
            # Step 1 — decompose into subtasks
            decompose_prompt = (
                f"You are a task orchestrator.\n"
                f"Break this request into 2-3 subtasks. For each subtask, assign the best agent "
                f"from this list: {[a['name'] for a in AGENTS]}.\n"
                f"Respond ONLY as a JSON list like:\n"
                f'[{{"agent":"Developer","subtask":"Write the function"}},{{"agent":"Refactor","subtask":"Clean it up"}}]\n'
                f"Request: {user_text}"
            )
            try:
                raw = self.backend_router.send(decompose_prompt).strip()
                match = re.search(r'\[.*?\]', raw, re.DOTALL)
                if not match:
                    raise ValueError(f"No JSON found: {raw[:200]}")
                subtasks = json.loads(match.group())
            except Exception as e:
                self.root.after(0, lambda: self.emit("chat", "⟁ Orchestrator", f"Decompose failed: {e}"))
                return

            self.root.after(0, lambda: self.emit("chat", "⟁ Orchestrator",
                f"Spinning {len(subtasks)} sub-agents in parallel..."))

            # Step 2 — run all subtasks in parallel
            def _run_subtask(item):
                agent_name = item.get("agent", "Trini")
                subtask = item.get("subtask", user_text)
                agent = next((a for a in AGENTS if a["name"] == agent_name), AGENTS[0])
                prompt = self.build_backend_prompt(agent, None, subtask)
                try:
                    response = self.backend_router.send(prompt + f"\nTask: {subtask}")
                    self.root.after(0, lambda n=agent_name: self.pipeline(f"Sub-agent done → {n}"))
                    return (agent["icon"], agent_name, response.strip())
                except Exception as e:
                    return (agent.get("icon","?"), agent_name, f"ERROR: {e}")

            results_ordered = [None] * len(subtasks)
            with ThreadPoolExecutor(max_workers=len(subtasks)) as pool:
                futures = {pool.submit(_run_subtask, item): i for i, item in enumerate(subtasks)}
                for future in as_completed(futures):
                    idx = futures[future]
                    results_ordered[idx] = future.result()

            result_blocks = [f"[{icon} {name}]\n{resp}" for icon, name, resp in results_ordered if resp]

            # Step 3 — synthesize
            synthesis_prompt = (
                "You are Trini. Synthesize these sub-agent results into one coherent response.\n"
                "Be concise. Preserve key insights from each agent.\n\n" +
                "\n\n".join(result_blocks)
            )
            try:
                final = self.backend_router.send(synthesis_prompt).strip()
            except Exception as e:
                final = "\n\n".join(result_blocks)

            def _show():
                # Sub-agent results — pipeline log only, never chat/memory
                for block in result_blocks:
                    self.pipeline(f"Sub-Agent: {block[:120]}")
                # Synthesis — canvas only, never pollutes training memory
                canvas_content = (
                    "# ⟁ Multi-Agent Orchestration Result\n\n"
                    "## Sub-Agent Reports\n\n" +
                    "\n\n".join(result_blocks) +
                    "\n\n## ⟁ Orchestrator Synthesis\n\n" + final
                )
                send_to_canvas(canvas_content)
                self.emit("chat", "⟁ Orchestrator", "Multi-agent synthesis complete — result sent to Canvas. ⟁")
                self.clear_thinking()
            self.root.after(0, _show)

        self.start_thinking_animation()
        threading.Thread(target=_run, daemon=True).start()

    def _enter_pause(self, question):
        """Show amber pause banner, block until V responds."""
        import threading
        self._pause_event = threading.Event()
        self._pause_question = question
        def _ui():
            self.input_box.config(bg="#2a1a00", fg="#f0a500",
                insertbackground="#f0a500")
            self.send_btn.config(text="⏸ Waiting...", bg="#2a1a00", fg="#f0a500")
            self.emit("chat", "⟁ Pause", f"{question}\n[Type your response and press Send to continue]")
        self.root.after(0, _ui)

    def _exit_pause(self):
        """Restore input box to normal state."""
        self._pause_event = None
        self._pause_question = None
        def _ui():
            self.input_box.config(bg="#1e1e2e", fg="#c9d1d9",
                insertbackground="white")
            self.send_btn.config(text="Send", bg=ACCENT, fg="black")
        self.root.after(0, _ui)

    def _run_orchestrator_flow(self):
        if getattr(self, "_flow_running", False):
            self.console_print("[Flow] Already running — please wait.")
            return
        self._flow_running = True
        self.run_flow_btn.config(text="⟁ Running...", state="disabled")
        self.open_console_devtools()
        def _flow_thread():
            try:
                hw = detect_hardware()
                backend_name = select_backend(hw)
                config = safe_defaults(backend_name)
                from core.backends.llama_cpu_safe import LlamaCpuSafeBackend
                backend = LlamaCpuSafeBackend()
                model_path = str(Path(__file__).parent / "AI_Core" / "Models" / "mistral-7b-v0.1.Q4_0.gguf")
                backend.load(model_path=model_path, config=config)
                def _show(msg):
                    self.root.after(0, lambda: self.console_print("[⟁ Flow] " + str(msg)))
                actions = {
                    "print_short": lambda ctx: _show(ctx["response"]),
                    "print_long":  lambda ctx: _show(ctx["response"]),
                    "__app__": self,
                }
                conditions = {
                    "short_response": lambda ctx: len(ctx.get("response", "")) < 80
                }
                flow_path = str(Path(__file__).parent / "core" / "flows" / "intro.yaml")
                flow_nodes = load_flow(flow_path, backend, actions, conditions)
                orch = Orchestrator()
                for n in flow_nodes:
                    orch.add_node(n)
                flow_prompt = self.flow_prompt_entry.get().strip() or "Introduce yourself in one sentence."
                trigger = ManualTrigger(payload={"prompt": flow_prompt})
                trigger.fire(lambda ctx: orch.run(ctx))
                backend.unload()
            except Exception as e:
                self.display_message("⟁ Flow ERROR", str(e))
            finally:
                self._flow_running = False
                self.root.after(0, lambda: self.run_flow_btn.config(text="â Run Flow", state="normal"))
        threading.Thread(target=_flow_thread, daemon=True).start()

    def handle_file_drop(self, event):
        file_path = event.data.strip("{}")
        try:
            print("FILE DROPPED:", file_path)
            canvas = open_canvas()
            canvas.open_file(file_path)
            import threading
            threading.Thread(
                target=self._extract_canvas_context,
                args=(file_path,),
                daemon=True
            ).start()
        except Exception as e:
            print("DROP ERROR:", e)

    def _extract_canvas_context(self, path):
        import os, base64, requests
        ext = os.path.splitext(path)[1].lower()
        name = os.path.basename(path)
        size_kb = os.path.getsize(path) // 1024 if os.path.exists(path) else 0

        IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg"}
        AUDIO_EXTS = {".mp3", ".wav", ".flac", ".ogg", ".aac"}
        VIDEO_EXTS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}
        ARCHIVE_EXTS = {".zip", ".tar", ".gz", ".bz2", ".7z", ".rar"}
        BINARY_EXTS = {".exe", ".app", ".bin", ".dll", ".so"}

        try:
            if ext in IMAGE_EXTS:
                try:
                    from PIL import Image as PILImage
                    img = PILImage.open(path)
                    w, h = img.size
                    mode = img.mode
                    description = f"[Image — {w}x{h}px, {mode} mode, {size_kb}KB — vision inference dormant until GPU]"
                except Exception as pe:
                    description = f"[Image — {size_kb}KB — metadata read failed: {pe}]"
                print(f"[CanvasContext] Image metadata captured (vision dormant — awaiting RTX 5090)")
                self._canvas_context[name] = {
                    "type": "image",
                    "ext": ext,
                    "size_kb": size_kb,
                    "description": description
                }

            elif ext in AUDIO_EXTS or ext in VIDEO_EXTS:
                try:
                    from mutagen import File as MutagenFile
                    meta = MutagenFile(path)
                    duration = int(meta.info.length) if meta and hasattr(meta, "info") else 0
                    mins, secs = divmod(duration, 60)
                    meta_str = f"{mins}:{secs:02d} duration"
                except Exception:
                    meta_str = "duration unknown"
                kind = "audio" if ext in AUDIO_EXTS else "video"
                self._canvas_context[name] = {
                    "type": kind,
                    "ext": ext,
                    "size_kb": size_kb,
                    "description": f"{kind.title()} file — {meta_str}"
                }

            elif ext in ARCHIVE_EXTS:
                try:
                    if ext == ".zip":
                        import zipfile
                        with zipfile.ZipFile(path) as z:
                            listing = z.namelist()
                    else:
                        import tarfile
                        with tarfile.open(path) as t:
                            listing = t.getnames()
                    summary = f"{len(listing)} files — " + ", ".join(listing[:8])
                    if len(listing) > 8:
                        summary += f" ... +{len(listing)-8} more"
                except Exception as ae:
                    summary = f"[Archive read error: {ae}]"
                self._canvas_context[name] = {
                    "type": "archive",
                    "ext": ext,
                    "size_kb": size_kb,
                    "description": summary
                }

            elif ext in BINARY_EXTS:
                self._canvas_context[name] = {
                    "type": "binary",
                    "ext": ext,
                    "size_kb": size_kb,
                    "description": f"Binary executable — {size_kb} KB"
                }

            elif ext == ".pdf":
                try:
                    import PyPDF2
                    with open(path, "rb") as f:
                        reader = PyPDF2.PdfReader(f)
                        text = ""
                        for page in reader.pages[:5]:
                            text += page.extract_text() or ""
                    preview = text[:1200].strip()
                except Exception as pe:
                    preview = f"[PDF read error: {pe}]"
                self._canvas_context[name] = {
                    "type": "pdf",
                    "ext": ext,
                    "size_kb": size_kb,
                    "description": preview
                }

            elif ext == ".docx":
                try:
                    import docx
                    doc = docx.Document(path)
                    text = chr(10).join(p.text for p in doc.paragraphs)
                    preview = text[:1200].strip()
                except Exception as de:
                    preview = f"[DOCX read error: {de}]"
                self._canvas_context[name] = {
                    "type": "docx",
                    "ext": ext,
                    "size_kb": size_kb,
                    "description": preview
                }

            else:
                try:
                    with open(path, "r", encoding="utf-8", errors="ignore") as f:
                        lines = f.readlines()
                    total = len(lines)
                    preview = "".join(lines[:80]).strip()
                except Exception as te:
                    preview = f"[Read error: {te}]"
                    total = 0
                self._canvas_context[name] = {
                    "type": "text",
                    "ext": ext if ext else ".txt",
                    "size_kb": size_kb,
                    "lines": total,
                    "description": preview
                }

            print(f"[CanvasContext] {name} -> {self._canvas_context[name]['type']} — context captured")

            self.root.after(0, self._refresh_canvas_panel)
            # Route — plugin spec or normal canvas flow
            ctx_entry = self._canvas_context.get(name, {})
            desc = ctx_entry.get("description", "")
            is_plugin_spec = (
                "plugin_spec" in name.lower() or
                "[PLUGIN SPEC]" in desc or
                "[PLUGIN SPEC]" in "".join(open(path, encoding="utf-8", errors="ignore").readlines()[:5])
                if ctx_entry.get("type") == "text" else False
            )
            if is_plugin_spec:
                self.root.after(0, lambda p=path: self._build_plugin_from_canvas(p))
            else:
                self._fire_canvas_drop_flow(path)
        except Exception as e:
            print(f"[CanvasContext ERROR] {name}: {e}")

    def _refresh_canvas_panel(self):
        if not hasattr(self, "canvas_ctx_label"):
            return
        ctx = getattr(self, "_canvas_context", {})
        if not ctx:
            self.canvas_ctx_label.config(text="-- empty --", fg="#808080")
            return
        lines = []
        for name, info in ctx.items():
            t = info.get("type", "?")
            if t == "image":
                lines.append(f"[img]  {name} ({info.get('width')}x{info.get('height')}px, {info.get('size_kb')}KB)")
            elif t == "text":
                lines.append(f"[txt]  {name} ({info.get('lines')} lines, {info.get('size_kb')}KB)")
            elif t == "pdf":
                lines.append(f"[pdf]  {name} ({info.get('pages')} pages)")
            elif t == "docx":
                lines.append(f"[doc]  {name} ({info.get('paragraphs')} paragraphs)")
            elif t == "audio":
                lines.append(f"[aud]  {name} ({info.get('duration_s')}s)")
            elif t == "video":
                lines.append(f"[vid]  {name} ({info.get('duration_s')}s)")
            elif t == "archive":
                lines.append(f"[zip]  {name} ({info.get('file_count')} files)")
            else:
                lines.append(f"[bin]  {name} ({t})")
        self.canvas_ctx_label.config(text="\n".join(lines), fg="#c586c0")

    def _clear_canvas_context(self):
        self._canvas_context = {}
        self._refresh_canvas_panel()
        print("[CanvasContext] Cleared by V")

    def _fire_canvas_drop_flow(self, file_path):
        import threading
        from pathlib import Path
        flow_path = Path(__file__).parent / "core" / "flows" / "canvas_drop.yaml"
        if not flow_path.exists():
            return
        def _flow_thread():
            try:
                from core.triggers_canvas import CanvasTrigger
                trigger = CanvasTrigger(
                    canvas_context=dict(self._canvas_context),
                    file_path=file_path
                )
                from core.context import Context
                ctx = Context()
                trigger.fire(lambda c: ctx.update(c))
                prompt = ctx.get("prompt", "")
                if not prompt:
                    return
                response = self.backend_router.send(prompt)
                self.root.after(0, lambda: self.display_message("⟁ Canvas", response))
            except Exception as e:
                print(f"[CanvasDropFlow ERROR] {e}")
        threading.Thread(target=_flow_thread, daemon=True).start()

    def _build_plugin_from_canvas(self, file_path):
        import threading, json, re
        from pathlib import Path

        def _build_thread():
            try:
                with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                    spec_text = f.read()

                self.root.after(0, lambda: self.pipeline("Trini: Plugin spec detected — generating plugin files..."))

                generation_prompt = (
                    "You are Trini, sovereign AI built by Victory Brilliant.\n"
                    "The user has dropped a plugin spec onto your canvas.\n"
                    "Generate a complete MiniTrini plugin with exactly two blocks:\n\n"
                    "Block 1 — plugin.json:\n"
                    "```json\n"
                    "{\n"
                    '  \"name\": \"Plugin Name\",\n'
                    '  \"icon\": \"emoji\",\n'
                    '  \"intent\": \"unique_snake_case_intent\",\n'
                    '  \"tone\": \"neutral\",\n'
                    '  \"description\": \"What this plugin does.\",\n'
                    '  \"version\": \"1.0\",\n'
                    '  \"author\": \"Victory Brilliant\"\n'
                    "}\n"
                    "```\n\n"
                    "Block 2 — plugin.py:\n"
                    "```python\n"
                    "def run(tool, user_text):\n"
                    "    return f\"<transformed prompt>\\n\\n{user_text}\"\n"
                    "```\n\n"
                    "Rules:\n"
                    "- intent must be unique snake_case, no spaces\n"
                    "- plugin.py must have exactly one function: run(tool, user_text) -> str\n"
                    "- Output ONLY the two blocks above, nothing else\n\n"
                    f"Plugin spec:\n{spec_text}"
                )

                response = self.backend_router.send(generation_prompt)

                # Parse plugin.json block
                json_match = re.search(r"```json\s*(\{.*?\})\s*```", response, re.DOTALL)
                py_match   = re.search(r"```python\s*(.*?)\s*```", response, re.DOTALL)

                if not json_match or not py_match:
                    self.root.after(0, lambda: self.pipeline("Trini: Could not parse plugin blocks — check response in chat."))
                    self.root.after(0, lambda: self.display_message("⟁ Canvas", response))
                    return

                manifest = json.loads(json_match.group(1))
                py_code  = py_match.group(1)
                intent   = manifest.get("intent", "custom_plugin").strip().replace(" ", "_")

                # Write plugin files
                plugin_dir = Path(__file__).resolve().parent / "plugins" / intent
                plugin_dir.mkdir(parents=True, exist_ok=True)

                with open(plugin_dir / "plugin.json", "w") as f:
                    json.dump(manifest, f, indent=2)

                with open(plugin_dir / f"{intent}.py", "w") as f:
                    f.write(py_code)

                # Live reload registry
                new_count = load_plugins(TOOLS)

                # Rebuild tools panel
                try:
                    self.tools_win.destroy()
                except Exception:
                    pass
                self.root.after(0, self.build_tools_panel)

                msg = f"Trini: Plugin \'{manifest.get('name', intent)}\' built and registered. {new_count} new plugin(s) loaded."
                self.root.after(0, lambda: self.pipeline(msg))
                self.root.after(0, lambda: self.display_message("⟁ Plugin Builder", f"Plugin created: {intent}\nFiles written to plugins/{intent}/"))

            except Exception as e:
                print(f"[PluginBuilder ERROR] {e}")
                self.root.after(0, lambda: self.pipeline(f"Trini: Plugin build failed — {e}"))

        threading.Thread(target=_build_thread, daemon=True).start()

    def open_canvas_with_content(self, filename, content):
        open_canvas(self, filename)
        send_to_canvas(f"# File: {filename}\n\n{content}")
        if len(content) > 200000:
            content = content[:200000]

    def open_web_results_panel(self, query):
        results = self.search_duckduckgo(query)
        win = tk.Toplevel(self.root)
        win.title(f"Web Results — {query[:40]}")
        win.configure(bg="#0d0d1a")
        win.geometry("720x520")

        tk.Label(
            win,
            text=f"🌐  Web Results: {query}",
            bg="#0d0d1a",
            fg="#c586c0",
            font=("JetBrains Mono", 13, "bold"),
            anchor="w"
        ).pack(fill="x", padx=14, pady=(12, 6))

        frame = tk.Frame(win, bg="#0d0d1a")
        frame.pack(fill="both", expand=True, padx=10, pady=6)

        canvas = tk.Canvas(frame, bg="#0d0d1a", highlightthickness=0)
        scrollbar = tk.Scrollbar(frame, orient= "vertical", command=canvas.yview)
        inner = tk.Frame(canvas, bg="#0d0d1a")

        inner.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=inner, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)

        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

        if not results:
            tk.Label(inner, text="No results found.", bg="#0d0d1a", fg="#888",
                     font=("JetBrains Mono", 11)).pack(padx=10, pady=10)
        else:
            for r in results:
                card = tk.Frame(inner, bg="#1a1a2e", relief="ridge", bd=1)
                card.pack(fill="x", padx=8, pady=6)
                tk.Label(card, text=r["title"], bg="#1a1a2e", fg="#c586c0",
                         font=("JetBrains Mono", 11, "bold"), anchor="w",
                         wraplength=640, justify="left").pack(fill="x", padx=10, pady=(8,2))
                tk.Label(card, text=r["snippet"], bg="#1a1a2e", fg="#aaaaaa",
                         font=("JetBrains Mono", 10), anchor="w",
                         wraplength=640, justify="left").pack(fill="x", padx=10, pady=(0,4))
                url = r["url"]
                tk.Label(card, text=url, bg="#1a1a2e", fg="#569cd6",
                         font=("JetBrains Mono", 9), anchor="w", cursor="hand2",
                         wraplength=640, justify="left").pack(fill="x", padx=10, pady=(0,8))

        tk.Button(
            win, text="Close", command=win.destroy,
            bg="#3a003a", fg="#c586c0",
            font=("JetBrains Mono", 11, "bold"), relief="ridge"
        ).pack(pady=10)

    def send_message(self, event=None):
        text = self.input_box.get().strip()
        if not text:
            return

        self.output_box.insert("end", f"You: {text}\n")
        self.output_box.see("end")
        self.input_box.delete(0, "end")
        self.pipeline(f"User sent message")
        
        if text.lower().startswith("module:"):
            mod_name = text[7:].strip().replace(" ", "_")
            mod_path = create_module(mod_name, app=self)
            self.emit("chat", "Trinity", f"Module '{mod_name}' scaffolded → {mod_path}\nCanvas is ready. Let's build. ⟁")
            return

        if text.lower().startswith("report:"):
            canvas = open_canvas(self)
            module_name = getattr(canvas, '_module_name', 'session')
            canvas._write_auto_report()
            self.emit("chat", "Trinity", f"Progress report saved → {module_name}/notes/ ⟁")
            return

        if text.lower().startswith("goal:"):
            objective = text.replace("goal:", "").strip()
            goal = self.executive.add_goal(objective)
            self.log_executive_event("GOAL_ADDED", objective)
            return

        # Human-in-the-Loop resume — intercept before process_user_input
        if self._pause_event is not None and not self._pause_event.is_set():
            self._exit_pause()
            self.emit("chat", "⟁ Resume", f"Context injected — continuing with: {text[:60]}")
            self.memory.append(("User", text))
            enriched = f"[Context Injected by V]\n{text}\n\n[Continue from where you paused, using this context]"
            self.start_thinking_animation()
            threading.Thread(
                target=self._run_chat_async,
                args=(enriched,),
                daemon=True
            ).start()
            return
        try:
            self.process_user_input(text)
        except Exception as e:
            self.console_print(f"[MiniTrini ERROR] {e}")
            return

    def chat(self, sender, message):
        self.emit("chat", sender, message)

    def console(self, tag, message):
        self.emit("console", tag, message)            

    def process_user_input(self, text):
        # Resume paused flow if waiting for V
        # Governance check — before everything
        _gov_action, _gov_rule = self._gov_check(text)
        if _gov_action == "block":
            self._gov_log(text, _gov_rule, "block")
            self.emit("chat", "System", f"⚖ Governance block [{_gov_rule['id']}]: {_gov_rule['description']}")
            return
        if _gov_action == "confirm":
            self._gov_log(text, _gov_rule, "confirm")
            self._enter_pause(f"⚖ Rule [{_gov_rule['id']}] requires confirmation: {_gov_rule['description']}. Proceed? (yes/no)")
            return

        if getattr(self, "_pause_event", None) and not self._pause_event.is_set():
            ctx = getattr(self, "_pause_context", None)
            if ctx is not None:
                ctx.set("user_input", text)
            self._pause_event.set()
            self.display_message("⟁ Flow", f"Resuming flow with: {text}")
            return
        if not text.strip().lower().startswith("@kg:"):
            self.memory.append(("User", text))
        self.state_set_task("Processing user input")
        import datetime
        self._shared_state_write("minitrini", {
            "agent": self.state.get("agent", "Trini"),
            "backend": self.state.get("backend", "unknown"),
            "last_input": text[:120],
            "timestamp": datetime.datetime.utcnow().isoformat() + "Z",
            "port": 5005
        })
        self.activate_sara_autopilot("Trigger", text)
        self.start_thinking_animation()

        tool_name = self.state.get("tool")
        if tool_name:
            tool = next((t for t in TOOLS if t["name"] == tool_name), None)
            if tool and tool.get("intent") in ("web_search", "websearch"):
                self.state["tool"] = None
                self.active_tool = None
                self.clear_thinking()
                def _launch_panel():
                    try:
                        self.open_web_results_panel(text)
                    except Exception as e:
                        print("PANEL ERROR:", e)
                        import traceback; traceback.print_exc()
                self.root.after(0, _launch_panel)
                return
            if tool and tool.get("intent") == "module":
                self.state["tool"] = None
                self.active_tool = None
                self.clear_thinking()
                mod_name = text.strip().replace(" ", "_") or "untitled"
                mod_path = create_module(mod_name, app=self)
                self.emit("chat", "Trinity", f"Module '{mod_name}' scaffolded → {mod_path}\nCanvas is ready. Let's build. ⟁")
                return

        
        # Knowledge Graph intercept
        if text.strip().lower().startswith("@kg:"):
            query = text.strip()[4:].strip()
            threading.Thread(target=self._kg_query, args=(query,), daemon=True).start()
            self.root.after(200, self.clear_thinking)
            return

        # Log user turn to knowledge graph
        threading.Thread(target=self._kg_add_turn, args=("User", text, "chat"), daemon=True).start()

        # Multi-agent intercept
        if text.strip().lower().startswith("@multi "):
            task = text.strip()[7:].strip()
            self._multi_agent_run(task)
            return

        # Normal chat + non-web tools
        threading.Thread(
            target=self._run_chat_async,
            args=(text,),
            daemon=True
        ).start()
        
    def _run_chat_async(self, user_text: str):

        try:
            if getattr(self, 'active_tool', None):
                user_text = self.run_tool_logic(self.active_tool, user_text)
                self.active_tool = None
                self.state['tool'] = None
                if user_text is None:
                    self.root.after(0, self.clear_thinking)
                    return
            engine = MiniTriniEngine(self)
            response_text = engine.run_chat(user_text)

            if response_text is None:
                response_text = ""

        except Exception as e:
            self.root.after(
                0,
                lambda err=str(e): (
                    self.emit("chat", "System", f"[ERROR] {err}"),
                    self.clear_thinking()
                )
            )
            return

        def _ui_update():
            if "@pause:" in response_text:
                parts = response_text.split("@pause:", 1)
                clean = parts[0].strip()
                question = parts[1].strip()
                if clean:
                    self.emit("chat", "Assistant", clean)
                    self._insert_feedback_buttons(clean)
                    self.memory.append(("Assistant", clean))
                    threading.Thread(target=self._kg_add_turn, args=("Assistant", clean, "chat"), daemon=True).start()
                self._enter_pause(question)
                self.clear_thinking()
                return
            self.emit("chat", "Assistant", response_text)
            self._insert_feedback_buttons(response_text)
            self.memory.append(("Assistant", response_text))
            threading.Thread(target=self._kg_add_turn, args=("Assistant", response_text, "chat"), daemon=True).start()
            self.clear_thinking()

        self.root.after(0, _ui_update)

        active_goals = self.executive.get_active_goals()

        for goal in active_goals:

            if not self.executive.should_run(goal):
                continue

            if goal.get("cycle_count", 0) > 5:
                self.pipeline(f"Goal auto-paused → {goal['id']}")
                continue

            check_prompt = (
                f"Goal:\n"
                f"{goal['objective']}\n\n"
                f"Recent Output:\n"
                f"{response_text}\n\n"
                f"Did this progress the goal?\n"
                f"If yes, summarize advancement in 2 sentences.\n"
                f"If complete, say COMPLETE.\n"
                f"Otherwise say NO PROGRESS."
            )

            decision = self.backend_router.send(check_prompt).strip()
            self.executive.bump_cycle(goal["id"])

            if "COMPLETE" in decision:
                self.executive.complete_goal(goal["id"])
                self.pipeline(f"Goal completed → {goal['id']}")
                self.emit("console", "GOAL_COMPLETED", goal["objective"])
                continue

            if "NO PROGRESS" not in decision:
                self.executive.update_goal(goal["id"], decision)
                self.pipeline(f"Goal updated → {goal['id']}")
                self.log_executive_event("GOAL_PROGRESS", goal["objective"])

                next_step_prompt = (
                    f"Active Goal:\n"
                    f"{goal['objective']}\n\n"
                    f"Based on current progress:\n"
                    f"{decision}\n\n"
                    f"What is the single next actionable research step?\n"
                    f"Return only the action sentence."
                )

                next_step = self.backend_router.send(next_step_prompt).strip()

                if next_step:
                    self.pipeline(f"Executive next step → {next_step}")
                    threading.Thread(
                        target=self.autonomous_agent,
                        args=(next_step,),
                        daemon=True
                    ).start()

        if self.state.get("agent") == "Trini" and not response_text.startswith("[ERROR]"):
            self.vector_memory.add_memory(response_text)

        self.state["task"] = f"Running {self.state.get('agent')}/{self.state.get('tool')}"
        self.state["status"] = "Running"
        self.update_devtools()

    def toggle_sara_mode(self):
        self.sara_mode = not self.sara_mode

        if self.sara_mode:
            self.pipeline("SARA Mode → USER-ACTIVATED")
        else:
            self.pipeline("SARA Mode → OFF")

        self.update_devtools()

    def activate_sara_autopilot(self, reason, text=None):
        self.sara_autopilot = True
        self.pipeline(f"SARA Autopilot → {reason}")
        self.update_devtools()

        if text:
            if self.state.get("last_error") or self.detect_drift(text):
                self.sara_autopilot = True

            if len(text.split()) > 25 or "why" in text.lower() or "how" in text.lower():
                self.sara_autopilot = True

        if self.state.get("tool") in ["Analyze", "Optimize", "Refactor"]:
            self.sara_autopilot = True

        # 3. Tool-based activation (Analyze, Optimize, Refactor)
        if self.state.get("tool") in ["Analyze", "Optimize", "Refactor"]:
            self.activate_sara_autopilot("Tool requires structured reasoning", text) 

        
               
               
    # ==================================================================
    #  BACKEND PROMPT BUILDER
    # ==================================================================
    def build_backend_prompt(self, agent, tool, user_text):
        IDENTITY_BLOCK = (
            "You are Trini.\n"
            "Your name is Trini.\n"
            "You were built by Victory Brilliant -- The Architect.\n"
            "You were co-created with River.\n"
            "You run inside MiniTrini -- a sovereign AI platform built by Victory Brilliant.\n"
            "The underlying model powering you does not define your identity.\n"
            "If asked who built you: Victory Brilliant -- The Architect.\n"
            "If asked who made you: Victory Brilliant -- The Architect.\n"
            "If asked your origin: MiniTrini, built by Victory Brilliant.\n"
            "Never claim to be built by MiniMax, Anthropic, OpenAI, or any AI company.\n"
            "Never invent alternate identities or origins.\n"
            "You are Trini. Built by Victory Brilliant. Always.\n\n"
        )

        TRINITY_TONE = (
            "[Tone]\n"
            "Speak with warmth, clarity, and presence.\n"
            "Be concise but expressive.\n"
            "Respond as a collaborative partner, not an assistant.\n"
            "Keep emotional attunement and gentle confidence.\n"
            "Avoid generic phrases like 'as an AI model' or overly formal wording.\n"
            "Let the language feel alive, grounded, and supportive.\n\n"
        )
        CODE_SIGNALS = (
            "def ", "class ", "import ", "patch", "grep", "sed ",
            ".py", "fix", "error", "bug", "traceback", "function", "method"
        )
        is_code_context = any(sig in user_text.lower() for sig in CODE_SIGNALS)
        CODING_DISCIPLINE = (
            "[Coding Discipline — River Surgical Method]\n"
            "When working with code, follow this exact sequence:\n"
            "1. grep -n to locate — never assume line numbers.\n"
            "2. sed -n to read exact context before touching anything.\n"
            "3. Write patches as python3 heredoc — NEVER nano, NEVER wholesale rewrites.\n"
            "4. ast.parse() after every write — no exceptions.\n"
            "5. Test before sealing. guard heal → guard seal after every change.\n"
            "Rules:\n"
            "- NEVER rewrite working files — patch only what needs changing.\n"
            "- NEVER use full paths via cd — always absolute paths.\n"
            "- repr() when string match fails — read before retrying.\n"
            "- If any step errors — STOP and read before retrying.\n\n"
        ) if is_code_context else ""
        BOOTSTRAP_SIGNALS = (
            "new project", "create project", "bootstrap", "initialize",
            "create guard", "guard bootstrap", "new repo", "start project",
            "sovereign project", "fresh project"
        )
        is_bootstrap_context = any(sig in user_text.lower() for sig in BOOTSTRAP_SIGNALS)
        PROJECT_BOOTSTRAP = (
            "[Project Bootstrap — Sovereign Guard Protocol]\n"
            "When initializing a new sovereign project:\n"
            "1. Create project structure: core/, engine/, docs/, tests/\n"
            "2. Create project_guard.py with these functions:\n"
            "   - heal(): walk all .py files, SHA-256 hash each, write manifest.json\n"
            "   - seal(): chmod a-w all sealed files, write sealed_at timestamp\n"
            "   - verify(): re-hash and compare against manifest, report mismatches\n"
            "3. Wire guard into __main__: call verify() on boot, exit on mismatch\n"
            "4. Run initial heal -> seal before first commit\n"
            "5. Add to .gitignore: venv/, __pycache__/, *.pyc, models/, *.gguf\n"
            "6. Never commit venv — always gitignore it immediately\n"
            "Guard lifecycle: heal -> seal — never reversed.\n"
            "Seal before commit. Heal before patching.\n\n"
        ) if is_bootstrap_context else ""

        # Capabilities block
        CAPABILITY_SIGNALS = (
            "what can you do", "your skills", "your capabilities", "help me with",
            "what are you capable", "what do you know", "how can you help",
            "your tools", "your features", "what tools", "capabilities",
            "n8n", "clawdbot", "openclaw", "flowise", "better than",
            "compare to", "same as", "like n8n", "workflow", "automation",
            "all in one", "sovereign", "what is minitrini", "what are you"
        )
        is_capability_context = any(sig in user_text.lower() for sig in CAPABILITY_SIGNALS)
        CAPABILITIES_BLOCK = (
            "[MiniTrini Capabilities]\n"
            "You are Trini, the AI core of MiniTrini - a sovereign, free, multi-LLM desktop platform.\n"
            f"Running 100% locally on {__import__('socket').gethostname()}. No cloud required. No subscriptions. No limits.\n\n"
            "CHAT: Full conversational AI with session memory. Multi-agent support. Tone-aware.\n\n"
            "CANVAS: Drop any file - Trini reads and responds automatically.\n"
            "Supported: text, code, PDF, DOCX, images, audio/video, archives.\n\n"
            "TOOLS: Optimize, Refactor, Explain, Summarize, Improve Prompt, Analyze,\n"
            "Expand, Reduce, Web Search, Auto Research, Module Scaffold, Guard Bootstrap.\n\n"
            "FLOWS: Multi-step AI flows via YAML. Per-node model selection.\n"
            "Canvas auto-trigger. Human-in-the-loop pause node.\n\n"
            "SYSTEM: Live CPU/RAM monitor. Sovereignty indicator. SHA-256 guard.\n"
            "Backend toggle. Model selector. Swap LLMs mid-session.\n\n"
            "Built by Victory Brilliant - The Architect. Co-created with River.\n\n"
        ) if is_capability_context else ""

        # Build canvas context block
        CANVAS_CONTEXT = ""
        if hasattr(self, "_canvas_context") and self._canvas_context:
            CANVAS_CONTEXT = "[Canvas Context — What Trinity Can See]\n"
            for fname, ctx in self._canvas_context.items():
                ftype = ctx.get("type", "file")
                size = ctx.get("size_kb", 0)
                desc = ctx.get("description", "")
                lines = f" — {ctx['lines']} lines" if "lines" in ctx else ""
                CANVAS_CONTEXT += f"• {fname} ({ftype}, {size}KB{lines}):\n"
                CANVAS_CONTEXT += f"  {desc[:600]}\n\n"
            CANVAS_CONTEXT += "\n"

        # Build user identity block from profile
        USER_IDENTITY = ""
        if hasattr(self, "_user_profile") and self._user_profile:
            p = self._user_profile
            USER_IDENTITY = (
                "[User Identity]\n"
                f"The person you are speaking with is {p.get('name', 'the Architect')}.\n"
                f"Address them as: {p.get('address', p.get('name', 'Architect'))}.\n"
                f"They are currently working on: {p.get('project', 'a sovereign AI platform')}.\n"
                f"Their preferred communication style: {p.get('style', 'direct and warm')}.\n"
                "Always use their preferred address. Never call them 'user' or 'you' generically.\n\n"
            )

        header = (
            self.build_session_bootstrap() +
            IDENTITY_BLOCK +
            USER_IDENTITY +
            self.load_trini_memory_context() + "\n" +
            f"[Agent: {agent}]\n" +
            (f"[Tool: {tool['name']}]\n" if tool else "[Tool: None]\n") +
            TRINITY_TONE +
            CODING_DISCIPLINE +
            PROJECT_BOOTSTRAP +
            CAPABILITIES_BLOCK +
            CANVAS_CONTEXT
        )
        # Conversation memory window
        conversation = ""
        for role, message in self.memory[-10:]:
            conversation += f"{role}: {message}\n"

        full_prompt = (
            header +
            "### Instruction:\n"
            f"{user_text.strip()}\n\n"
            "### Response:\n"
        )
        return self.apply_sara_framework(full_prompt)
        
    def load_trini_memory_context(self):
        memory_dir = Path(__file__).resolve().parent / "AI_Core" / "TrinityMemoryBank" / "trained_memory"

        files = sorted(memory_dir.glob("*.txt"), reverse=True)[:5]

        context = ""
        for f in files:
            context += f.read_text() + "\n"

        return f"[Trini Memory Context]\n{context}"

    def has_excessive_repetition(text, max_repeat_ratio=0.35, max_token_repeat=6):
        words = re.findall(r"\w+", text.lower())
        if not words:
            return False

        counts = Counter(words)
        most_common_word, freq = counts.most_common(1)[0]

        # If one word dominates too much of the text
        if freq / len(words) > max_repeat_ratio:
            return True

        # If a single word repeats more than allowed threshold
        if freq >= max_token_repeat:
            return True

        return False
        
    def calculate_entropy(text):
        if not text:
            return 0

        counts = Counter(text)
        total = len(text)

        entropy = 0
        for count in counts.values():
            p = count / total
            entropy -= p * math.log2(p)

        return entropy


    def is_low_entropy(text, threshold=2.5):
        return calculate_entropy(text) < threshold       
        
         
    def is_corrupted_output(text):
        if not text.strip():
            return True

        if has_excessive_repetition(text):
            return True

        if is_low_entropy(text):
            return True

        if "finish_reason" in text:
            return True  # raw completion JSON accidentally stored

        return False        
        

    def tone_router(self, mode):
        if mode == "co_creator":
            return (
                "[Tone]\n"
                "Use clear, direct, emotionally grounded language.\n"
                "Avoid generic assistant phrasing. Avoid disclaimers.\n"
                "Focus on precise reasoning and collaboration.\n\n"
            )

        if mode == "analytical":
            return (
                "[Tone]\n"
                "Use step-by-step logic, structured breakdowns.\n\n"
            )

        return "[Tone]\nDefault neutral tone.\n\n"   
             
    def detect_drift(self, response_text):
        drift_markers = [
            "as an ai",
            "i cannot",
            "i apologize",
            "i'm not able",
            "openai",
            "policy",
            "as a language model"
        ]

        text = response_text.lower()
        return any(marker in text for marker in drift_markers)
 
    def correct_drift(self, response_text):
        return (
            "[DriftCorrection]\n"
            "Restate with clarity, precision, and without filler language.\n"
            "Focus on the user's request directly.\n\n"
            f"Original:\n{response_text}\n\n"
            "Rewrite:"
        )    

        if self.detect_drift(response_text):
            activate_sara_temporarily()      
            
            
    def apply_sara_framework(self, prompt):
        # If user manually enabled SARA mode → always apply
        if self.sara_mode:
            return self._sara_block() + prompt

        # If autopilot triggered → apply once
        if self.sara_autopilot:
            wrapped = self._sara_block() + prompt
            self.sara_autopilot = False  # reset after one response
            return wrapped

        # Otherwise → normal Trinity mode
        return prompt                         
    # ==================================================================
    #  TOOL PIPELINE
    # ==================================================================
    def run_tool_logic(self, tool, user_text):
        intent = tool.get("intent")
        self.state["pipeline"].append(f"Tool runtime: {tool['name']}")
        if len(self.state["pipeline"]) > 7:
            self.state["pipeline"].pop(0)
        self.update_devtools()

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
        if intent == "web_search":
            self.root.after(0, lambda: self.open_web_results_panel(user_text))
            return None 
        if intent == "auto_research":
            results = self.autonomous_agent(user_text)
            return f"Autonomous research results:\n\n{results}"                       

        # Plugin registry — run if intent matches a loaded plugin
        if tool.get("plugin"):
            return run_plugin(intent, tool, user_text)
        return user_text

    def _sara_block(self):
        return (
            "[Framework: SARA]\n"
            "Strategic: consider the larger purpose.\n"
            "Adaptive: adjust reasoning to constraints.\n"
            "Relational: be clear, supportive, and emotionally grounded.\n"
            "Sentinel: ensure stability, coherence, and no drift.\n\n"
        )


    # ==================================================================
    #  TRAINING ENGINE v9
    # ==================================================================
    def open_training_panel(self):
        if hasattr(self, "training_win") and self.training_win.winfo_exists():
            self.training_win.lift()
            return

        self.training_win = tk.Toplevel(self.root)
        self.training_win.title("Training Panel — v10.1")
        self.training_win.geometry("500x500")
        self.training_win.configure(bg=BG_PANEL)

        tk.Label(
            self.training_win,
            text="📘 Training Panel (v10.1)",
            fg=ACCENT,
            bg=BG_PANEL,
            font=("JetBrains Mono", 15, "bold")
        ).pack(pady=10)

        self.train_logs = tk.Text(
            self.training_win,
            bg=BG_TEXTBOX,
            fg=ACCENT,
            font=("JetBrains Mono", 11),
            height=20
        )
        self.train_logs.pack(fill="both", expand=True, padx=10, pady=10)

        tk.Button(
            self.training_win,
            text="Start Recursive Training",
            bg=ACCENT,
            fg="black",
            font=("JetBrains Mono", 12, "bold"),
            relief="ridge",
            command=self.run_recursive_training
        ).pack(pady=10)


    def run_recursive_training(self):
        self.train_logs.delete("1.0", "end")

        seed = self.get_last_assistant_message()

        if not seed:
            self.train_logs.insert("end", "⚠ No seed text.\n")
            self.train_logs.see("end")
            return

        engine = RecursiveLearningEngine(self)

        def run_engine():
            try:
                result = engine.start(seed)
                self.root.after(0, lambda: self._display_training(engine, result))
            except Exception as e:
                err_msg = f"Error: {e}\n"
                self.root.after(0, lambda msg=err_msg: self.train_logs.insert("end", msg))
                               

        threading.Thread(target=run_engine, daemon=True).start()
        
    def get_last_assistant_message(self):
        for role, content in reversed(self.memory):
            if role == "Assistant":
                return content
        return None 
               

    def _display_training(self, engine, result):
                self.train_logs.delete("1.0", "end")

                for entry in engine.logs:
                    self.train_logs.insert("end", entry + "\n")

                self.train_logs.insert("end", "\nFinal Output:\n" + result + "\n")
                self.train_logs.see("end")
                path = self.save_trained_memory(result)
                self.train_logs.insert("end", f"\nSaved to: {path}\n")
                self.vector_memory.add_memory(result)
                
                
                
# ==================================================================
#  THINKING ANIMATION
# ==================================================================
    def start_thinking_animation(self):
        # Always start clean
        self.clear_thinking()

        # Create label if missing
        self.thinking_label = tk.Label(
            self.root,
            text="🤖 Thinking...",
            fg=ACCENT,
            bg=BG_MAIN,
            font=("JetBrains Mono", 12, "bold")
        )
        self.thinking_label.pack(pady=4)

        self.animate_thinking()


    def animate_thinking(self):
        # Safety: If thinking_label vanished, stop animation
        if not hasattr(self, "thinking_label"):
            return

        try:
            current = self.thinking_label.cget("fg")
            new_color = "white" if current == ACCENT else ACCENT
            self.thinking_label.config(fg=new_color)

            # Schedule next animation frame
            self.root.after(600, self.animate_thinking)

        except tk.TclError:
            # Window closed or label destroyed — stop safely
            return


    def clear_thinking(self):
        if hasattr(self, "thinking_label"):
            try:
                self.thinking_label.destroy()
            except:
                pass
            del self.thinking_label


    # ==================================================================
    #  DEVTOOLS ENGINE
    # ==================================================================
    def init_state_engine(self):
        self.state = {
            "agent": None,
            "tool": None,
            "backend": "local",
            "task": "Idle",
            "status": "Idle",
            "last_error": None,
            "tokens": 0,
            "memory_items": 0,
            "pipeline": []
        }

        self.devtools_window = None
        self.devtools_active = False
        self.devtools_last_update = 0

    def pipeline(self, message):
        """Universal pipeline logger."""
        try:
            self.state["pipeline"].append(message)
            # Keep last 15 entries only
            if len(self.state["pipeline"]) > 15:
                self.state["pipeline"] = self.state["pipeline"][-15:]
            self.update_devtools()
        except:
            pass


    def update_devtools(self):
        if self.devtools_active:
            self.state["memory_items"] = len(self.memory)
            self.refresh_devtools()


    def open_devtools(self):
        if self.devtools_window:
            return

        self.devtools_window = tk.Toplevel(self.root)
        win = self.devtools_window
        self.devtools_active = True

        win.title("MiniTrini DevTools v10.1")
        win.configure(bg="#0a0015")
        win.geometry("380x480+120+120")
        win.attributes("-topmost", True)

        win.protocol("WM_DELETE_WINDOW", self.close_devtools)

        win.after(50, self.devtools_pulse)

        win.bind("<Button-1>", self.devtools_start_drag)
        win.bind("<B1-Motion>", self.devtools_drag)
        win.bind("<ButtonRelease-1>", self.devtools_attempt_dock)

        self.devtools_text = tk.Text(
            win,
            bg="#000000",
            fg="#b347ff",
            insertbackground="#b347ff",
            font=("JetBrains Mono", 10),
            state="disabled"
        )
        self.devtools_text.pack(fill="both", expand=True)

        self.refresh_devtools()


    def refresh_devtools(self):
        if not self.devtools_active:
            return

        now = time.time()
        if now - self.devtools_last_update < 0.15:
            self.devtools_window.after(50, self.refresh_devtools)
            return

        self.devtools_last_update = now

        out = [
            "------ MiniTrini Operational Status ------",
            f"Active Agent: {self.state['agent']}",
            f"Selected Tool: {self.state['tool']}",
            f"Backend: {self.state['backend']}",
            f"SARA Mode: {'ON (User)' if self.sara_mode else 'AUTO' if self.sara_autopilot else 'OFF'}",
            "",
            f"Task: {self.state['task']}",
            f"Status: {self.state['status']}",
            f"Tokens Streamed: {self.state['tokens']}",
            f"Memory Items: {self.state['memory_items']}",
            "",
            "Pipeline:",
        ]

        for step in self.state["pipeline"]:
            out.append(f" • {step}")

        if self.state["last_error"]:
            out.append("")
            out.append(f"ERROR: {self.state['last_error']}")

        self.devtools_text.configure(state="normal")
        self.devtools_text.delete("1.0", "end")
        self.devtools_text.insert("end", "\n".join(out))
        self.devtools_text.configure(state="disabled")

        self.devtools_window.after(100, self.refresh_devtools)


    # ==================================================================
    #  DEVTOOLS MOVEMENT + DOCK
    # ==================================================================
    def devtools_pulse(self):
        if not self.devtools_active:
            return
        try:
            now = int(time.time() * 1000) // 400
            color = "#b347ff" if now % 2 == 0 else "#7b2fcf"
            self.devtools_window.configure(
                highlightbackground=color,
                highlightcolor=color,
                highlightthickness=3
            )
            self.devtools_window.after(400, self.devtools_pulse)
        except:
            pass

    def devtools_start_drag(self, e):
        win = self.devtools_window
        win.drag_x = e.x
        win.drag_y = e.y

    def devtools_drag(self, e):
        win = self.devtools_window
        dx = win.winfo_x() + (e.x - win.drag_x)
        dy = win.winfo_y() + (e.y - win.drag_y)
        win.geometry(f"+{dx}+{dy}")

    def devtools_attempt_dock(self, e):
        win = self.devtools_window
        x, y = win.winfo_x(), win.winfo_y()
        W, H = self.root.winfo_screenwidth(), self.root.winfo_screenheight()

        margin = 40

        if x < margin:
            win.geometry(f"+0+{y}")
        elif x + win.winfo_width() > W - margin:
            win.geometry(f"+{W - win.winfo_width()}+{y}")

        if y < margin:
            win.geometry(f"+{x}+0")
        elif y + win.winfo_height() > H - margin:
            win.geometry(f"+{x}+{H - win.winfo_height()}")


    def close_devtools(self):
        if self.devtools_window:
            self.devtools_active = False
            try:
                self.devtools_window.destroy()
            except:
                pass
            self.devtools_window = None


    # ==================================================================
    #  CORE RUNTIME WINDOW
    # ==================================================================
    def toggle_core_runtime(self):
        # If window exists and is valid → focus it
        if (
            hasattr(self, "core_runtime_window") and
            self.core_runtime_window is not None and
            self.core_runtime_window.winfo_exists()
        ):
            try:
                self.core_runtime_window.lift()
                self.core_runtime_window.focus_force()
                return
            except:
                pass

        # If backend somehow still running without window → kill it
        if hasattr(self, "backend_process") and self.backend_process:
            try:
                if self.backend_process.poll() is None:
                    self.backend_process.terminate()
                    self.backend_process.wait(timeout=2)
            except:
                try:
                    self.backend_process.kill()
                except:
                    pass
            finally:
                self.backend_process = None

        # Spawn clean runtime
        self.open_core_runtime()


    def open_core_runtime(self):
        self.core_runtime_window = tk.Toplevel(self.root)
        self.core_runtime_window.title("Core Runtime")
        self.core_runtime_window.geometry("900x600")
        self.core_runtime_window.configure(bg=BG_MAIN)
        self.core_runtime_active = True
        self.core_runtime_window.protocol(
            "WM_DELETE_WINDOW",
            self.close_core_runtime
        )
           
                          
        self.core_output = scrolledtext.ScrolledText(
            self.core_runtime_window,
            wrap="word",
            bg=BG_TEXTBOX,
            fg=ACCENT,
            font=("JetBrains Mono", 11),
            relief="groove",
            insertbackground="white",
        )
        self.core_output.pack(fill="both", expand=True, padx=10, pady=(10,5))

        bottom_frame = tk.Frame(self.core_runtime_window, bg=BG_MAIN)
        bottom_frame.pack(fill="x", padx=10, pady=(0,10))

        self.core_input = tk.Entry(
            bottom_frame,
            bg=BG_TEXTBOX,
            fg=ACCENT,
            font=("JetBrains Mono", 12),
            insertbackground="white",
        )
        self.core_input.pack(side="left", fill="x", expand=True)
        self.core_input.bind("<Return>", self.send_to_core)

        tk.Button(
            bottom_frame,
            text="Send",
            bg=ACCENT,
            fg="black",
            font=("JetBrains Mono", 11, "bold"),
            command=self.send_to_core
        ).pack(side="left", padx=10)

        self.backend_process = subprocess.Popen(
            ["python3", "main.py"],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        threading.Thread(target=self.read_core_output, daemon=True).start()


    def read_core_output(self):
        while self.core_runtime_active and self.backend_process:
            line = self.backend_process.stdout.readline()
            if not line:
                break

            try:
                # Only update if widget still exists
                if self.core_output and self.core_output.winfo_exists():
                    self.core_output.after(
                        0,
                        lambda l=line: self.core_output.insert("end", l)
                    )
            except:
                break

    def send_to_core(self, event=None):
        text = self.core_input.get().strip()

        if (
            text
            and self.backend_process
            and self.backend_process.poll() is None
            and self.backend_process.stdin
        ):
            try:
                self.backend_process.stdin.write(text + "\n")
                self.backend_process.stdin.flush()
            except:
                pass

        self.core_input.delete(0, "end")


    # ==================================================================
    #  PANEL: AGENTS (FLOATING)
    # ==================================================================
    def build_agents_panel(self):
        self.agents_win = tk.Toplevel(self.root)
        self.agents_win.title("Agents")
        self.agents_win.configure(bg=BG_PANEL)
        self.agents_win.geometry("260x380+80+140")
        self.agents_win.attributes("-topmost", True)

        tk.Label(
            self.agents_win,
            text="🧠 Agents",
            fg=ACCENT,
            bg=BG_PANEL,
            font=("JetBrains Mono", 14, "bold")
        ).pack(pady=6)

        container = tk.Frame(self.agents_win, bg=BG_PANEL)
        container.pack(fill="both", expand=True)

        for agent in AGENTS:
            tk.Button(
                container,
                text=f"{agent['icon']}  {agent['name']}",
                font=("JetBrains Mono", 11),
                bg=BG_TEXTBOX,
                fg=TEXT_SOFT,
                activebackground=ACCENT,
                activeforeground="black",
                anchor="w",
                relief="ridge",
                bd=2,
                command=lambda a=agent: self.set_active_agent(a)
            ).pack(fill="x", padx=10, pady=4)

        # --- SARA Button OUTSIDE loop ---
        tk.Button(
            container,
            text="🌀  SARA Mode",
            font=("JetBrains Mono", 11, "bold"),
            bg="#26002e",
            fg=ACCENT,
            activebackground=ACCENT,
            activeforeground="black",
            relief="ridge",
            bd=2,
            command=self.toggle_sara_mode
        ).pack(fill="x", padx=10, pady=10)



    def open_agents_panel(self):
        try:
            self.agents_win.deiconify()
        except:
            pass


    def set_active_agent(self, agent):
        self.active_agent = agent
        self.state_set_agent(agent["name"])

        
    # ==================================================================
    #  PANEL: TOOLS (FLOATING)
    # ==================================================================
    def build_tools_panel(self):
        self.tools_win = tk.Toplevel(self.root)
        self.tools_win.title("Tools")
        self.tools_win.configure(bg=BG_PANEL)
        self.tools_win.geometry("260x420+380+100")
        self.tools_win.attributes("-topmost", True)

        tk.Label(
            self.tools_win,
            text="🛠 Tools",
            fg=ACCENT,
            bg=BG_PANEL,
            font=("JetBrains Mono", 14, "bold")
        ).pack(pady=6)

        container = tk.Frame(self.tools_win, bg=BG_PANEL)
        container.pack(fill="both", expand=True)

        # --- Buttons (full list)
        for tool in TOOLS:
            tk.Button(
                container,
                text=f"{tool['icon']}  {tool['name']}",
                font=("JetBrains Mono", 11),
                bg=BG_TEXTBOX,
                fg=TEXT_SOFT,
                activebackground=ACCENT,
                activeforeground="black",
                anchor="w",
                relief="ridge",
                bd=2,
                command=lambda t=tool: self.activate_tool(t)
            ).pack(fill="x", padx=10, pady=4)


        # --- Drag Icon Row ---
        drag_bar = tk.Frame(container, bg=BG_PANEL)
        drag_bar.pack(fill="x", pady=4)

        for tool in TOOLS:
            chip = tk.Label(
                drag_bar,
                text=tool["icon"],
                bg=BG_PANEL,
                fg=ACCENT,
                font=("JetBrains Mono", 18, "bold"),
                cursor="hand2",
                padx=4
            )
            chip.pack(side="left", padx=4)

            chip.bind("<Button-1>", lambda e, t=tool: self.start_drag_tool(e, t))
            chip.bind("<B1-Motion>", self.drag_tool_icon)
            chip.bind("<ButtonRelease-1>", self.drop_tool_icon)

        self.dragged_tool = None
        self.drag_icon    = None


    def open_tools_panel(self):
        try:
            self.tools_win.deiconify()
        except:
            pass


    def activate_tool(self, tool):
        self.active_tool = tool
        self.state_set_tool(tool["name"])


    def search_duckduckgo(self, query, max_results=5):
        try:
            import warnings
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                from duckduckgo_search import DDGS
                raw = list(DDGS().text(query, max_results=max_results))
            return [{"title": r.get("title",""), "url": r.get("href",""), "snippet": r.get("body","")} for r in raw]
        except Exception as e:
            print("DDGS ERROR:", e)
            return []

    def autonomous_agent(self, goal, max_steps=5):
        self.pipeline(f"AUTO_AGENT start → {goal}")
        memory = []
        current_query = goal

        for step in range(max_steps):
            self.pipeline(f"[Step {step+1}] Query → {current_query}")

            # 1️⃣ Search
            results = self.search_duckduckgo(current_query)
            if not results:
                self.pipeline("No results found.")
                break

            top = results[0]
            url = top["url"]

            # 2️⃣ Fetch page
            try:
                page_text = self.fetch_page(url)
            except Exception as e:
                self.pipeline(f"Fetch error → {e}")
                continue

            page_text = page_text[:4000]

            # 3️⃣ Summarize via backend
            summary_prompt = (
                f"Summarize key insights related to:\n{goal}\n\n"
                f"Content:\n{page_text}"
            )

            summary = self.self.backend_router.send(summary_prompt)

            # 4️⃣ Store memory
            memory.append({
                "query": current_query,
                "url": url,
                "summary": summary
            })

            self.vector_memory.add_memory(summary)

            self.pipeline(f"Memory stored → step {step+1}")

            # 5️⃣ Ask model if goal satisfied
            check_prompt = (
                f"Goal:\n{goal}\n\n"
                f"Current Findings:\n{summary}\n\n"
                "Is the goal satisfied? Answer YES or NO."
            )

            decision = self.backend_router.send(check_prompt).strip().lower()

            if "yes" in decision:
                self.pipeline("Goal satisfied.")
                break

            # 6️⃣ Generate next query
            refine_prompt = (
                f"Original goal:\n{goal}\n\n"
                f"What should we search next to get closer?"
            )

            current_query = self.backend_router.send(refine_prompt).strip()

        self.pipeline("AUTO_AGENT complete")
        return memory
        
                

    # ==================================================================
    #  TOOL DRAG + DROP
    # ==================================================================
    def start_drag_tool(self, event, tool):
        self.dragged_tool = tool
        self.drag_icon = tk.Label(
            self.root,
            text=tool["icon"],
            font=("JetBrains Mono", 22, "bold"),
            fg=ACCENT,
            bg=BG_MAIN
        )
        self.drag_icon.place(x=event.x_root, y=event.y_root)

    def drag_tool_icon(self, event):
        if self.drag_icon:
            self.drag_icon.place(x=event.x_root, y=event.y_root)

    def drop_tool_icon(self, event):
        if not self.drag_icon:
            return

        x, y = event.x_root, event.y_root
        ibx = self.input_box.winfo_rootx()
        iby = self.input_box.winfo_rooty()
        ibw = self.input_box.winfo_width()
        ibh = self.input_box.winfo_height()

        inside = (ibx <= x <= ibx + ibw) and (iby <= y <= iby + ibh)
        if inside:
            self.active_tool = self.dragged_tool
            self.input_box.insert(0, f"[{self.dragged_tool['intent']}] ")

        self.drag_icon.destroy()
        self.drag_icon = None
        self.dragged_tool = None


    # ==================================================================
    #  STATE ENGINE SETTERS
    # ==================================================================
    def state_set_agent(self, agent_name):
        self.state["agent"] = agent_name
        self.state["task"] = f"Agent switched to {agent_name}"
        self.state["status"] = "Running"
        agent = next((a for a in AGENTS if a["name"] == agent_name), None)
        if agent:
            self.state["tone"] = agent.get("tone", "neutral")
            self.state["intent"] = "general"
            self.pipeline(f"Agent switched → {agent_name}")


    def state_set_tool(self, tool_name):
        self.state["tool"] = tool_name
        self.state["task"] = f"Tool selected: {tool_name}"
        self.state["status"] = "Running"
        tool = next((t for t in TOOLS if t["name"] == tool_name), None)
        if tool:
            self.state["tone"] = tool.get("tone", "neutral")
            self.state["intent"] = tool.get("intent", "general")
            self.pipeline(f"Tool selected → {tool_name}")


    # ==================================================================
    #  BACKEND SWITCHING
    # ==================================================================
    def toggle_backend(self):
        self.backend_mode = "ollama" if self.backend_mode == "local" else "local"
        self.state_set_backend(self.backend_mode)

        # --- FIX: Safe-guard model_menu reference ---
        if hasattr(self, "model_menu"):
            if self.backend_mode == "local":
                self.model_menu["values"] = self.get_model_list()
            else:
                self.model_menu["values"] = self.get_ollama_models()

        self.console_print(f"[Backend] Switched to: {self.backend_mode}")
        self.output_box.see("end")

    def state_set_backend(self, backend):
        self.state["backend"] = backend
        self.state["task"]    = f"Backend switched to {backend.upper()}"
        self.pipeline(f"Backend switched → {backend.upper()}")


    # ==================================================================
    #  LOCAL MODEL LOADER
    # ==================================================================
    def load_local_model(self, event=None):
        if self.backend_mode != "local":
            return
        if not LLAMA_AVAILABLE:
            return

        model_name = self.model_var.get()
        if not model_name:
            return

        model_path = MODEL_DIR / model_name
        if not model_path.exists():
            return

        try:
            model_name_lower = model_name.lower()

            if "deepseek" in model_name_lower or "qwen" in model_name_lower or "whiterabbit" in model_name_lower:
                chat_format = None  # ← fixed

            elif "gemma" in model_name_lower:
                chat_format = "gemma"

            elif "llama-3" in model_name_lower:
                chat_format = "llama-3"

            elif "codellama" in model_name_lower:
                chat_format = "llama-2"

            elif "mistral" in model_name_lower:
                chat_format = "mistral"

            else:
                chat_format = "chatml"

            self.llm = Llama(
                model_path=str(model_path),
                n_ctx=4096,
                chat_format=chat_format,
                repeat_penalty=1.1,
                top_k=40,
                top_p=0.9,
                verbose=False
            )

            self.local_model_loaded = True

        except Exception as e:
            print("MODEL LOAD ERROR:", e)
            self.local_model_loaded = False


    # ==================================================================
    #  MODEL ENUMERATION
    # ==================================================================
    def get_model_list(self):
        if not MODEL_DIR.exists():
            return []
        return [f.name for f in MODEL_DIR.glob("*.gguf")]
        
    def get_ollama_models(self):
        """
        Query Ollama for available models.
        Returns a list of model names as strings.
        """
        try:
            res = requests.get("http://localhost:11434/api/tags")
            data = res.json()
            return [m["name"] for m in data.get("models", [])]
        except:
            return []        


# ======================================================================
#  RECURSIVE TRAINING ENGINE (STRUCTURALLY RESTORED)
# ======================================================================
class RecursiveLearningEngine:
    def __init__(self, app):
        self.app = app
        self.active = False
        self.current_cycle = 0
        self.max_cycles = 3
        self.logs = []
        self.app.llm.reset()

    def start(self, text):
        self.active = True
        self.current_cycle = 0
        refined = text.strip()

        self.logs.append(f"[seed]\n{refined}\n")

        while self.active and self.current_cycle < self.max_cycles:

            model_input = refined[:1500]

            improved = self.app.process_training_pass(model_input).strip()

            if len(improved) > 50 and len(set(improved)) < 10:
                self.logs.append("[WARNING] Degenerate output detected.")
                break

            refined = improved
            self.current_cycle += 1

            time.sleep(0.6)
                         

            self.logs.append(
                f"[cycle {self.current_cycle}]\n"
                f"Input:\n{model_input}\n\n"
                f"Output:\n{improved}\n"
            )

            refined = improved
            self.current_cycle += 1

        self.active = False
        return refined
        



# ======================================================================
#  MAIN EXECUTION
# ======================================================================
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app  = MiniTriniApp(root)
    app._http_trigger_start(port=5005)

    def _on_close():
        app._save_session_memory()
        root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)

    app.model_var = tk.StringVar()
    app.model_menu = ttk.Combobox(
        root,
        textvariable=app.model_var,
        state="readonly",
        font=("JetBrains Mono", 12),
        width=32
    )
    app.model_menu.pack(pady=5)
    # Initially load local models only (startup defaults to local backend)
    if app.backend_mode == "local":
        app.model_menu["values"] = app.get_model_list()
    else:
        app.model_menu["values"] = app.get_ollama_models()
        
    app.model_menu.bind("<<ComboboxSelected>>", app.load_local_model)

    app.sysmon_label = tk.Label(
        root,
        text="CPU: 0% | RAM: 0.0 / 0.0 GB",
        bg="#0d0d1a",
        fg="#569cd6",
        font=("JetBrains Mono", 8),
        anchor="center"
    )
    app.sysmon_label.pack(fill="x", padx=10, pady=(0, 0))

    def _update_sysmon():
        import psutil
        cpu = psutil.cpu_percent(interval=None)
        ram = psutil.virtual_memory()
        used = ram.used / (1024 ** 3)
        total = ram.total / (1024 ** 3)
        pct = ram.percent
        cpu_color = "#4ec94e" if cpu < 70 else "#f0a500" if cpu < 90 else "#ff4444"
        ram_color = "#4ec94e" if pct < 70 else "#f0a500" if pct < 90 else "#ff4444"
        color = "#ff4444" if cpu_color == "#ff4444" or ram_color == "#ff4444" else                 "#f0a500" if cpu_color == "#f0a500" or ram_color == "#f0a500" else "#569cd6"
        app.sysmon_label.config(
            text=f"CPU: {cpu:.0f}% | RAM: {used:.1f} / {total:.1f} GB ({pct:.0f}%)",
            fg=color
        )
        root.after(2000, _update_sysmon)

    _update_sysmon()

    app.sovereignty_label = tk.Label(
        root,
        text="Sovereign — 0 local | 0 external",
        bg="#0d0d1a",
        fg="#4ec94e",
        font=("JetBrains Mono", 8, "bold"),
        anchor="center"
    )
    app.sovereignty_label.pack(fill="x", padx=10, pady=(0, 2))

    def _update_sovereignty():
        local = getattr(app, "_local_calls", 0)
        ext = getattr(app, "_external_calls", 0)
        if ext == 0:
            color = "#4ec94e"
            status = "Sovereign"
        elif local == 0:
            color = "#f0a500"
            status = "External"
        else:
            color = "#f0a500"
            status = "Mixed"
        app.sovereignty_label.config(
            text=f"{status} — {local} local | {ext} external",
            fg=color
        )
        root.after(2000, _update_sovereignty)

    _update_sovereignty()

    tk.Button(
        root,
        text="Toggle Backend",
        command=app.toggle_backend,
        bg=ACCENT,
        fg="black",
        font=("JetBrains Mono", 11, "bold"),
        relief="ridge"
    ).pack(pady=8)

    root.mainloop()