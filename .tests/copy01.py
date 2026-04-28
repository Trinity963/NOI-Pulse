#!/usr/bin/env python3
# MiniTrini_v10.1 — Trinity Multi-Agent Edition with Pulse Glow + Training Engine


import time
import math
import tkinter as tk
import tkinter.simpledialog as sd
from tkinter import ttk, scrolledtext
from datetime import datetime
import json, os, stat, requests
from pathlib import Path
import sys
import subprocess
import threading
from subprocess import PIPE
import re
import platform
from sentence_transformers import SentenceTransformer
model = SentenceTransformer("all-MiniLM-L6-v2")
from AI_Core.TrinityMemoryBank.trini_vector_memory import TriniVectorMemory
import inspect
from AI_Core.Executive.trini_executive import TriniExecutive
from TrinityCanvas import  send_to_canvas 
from bs4 import BeautifulSoup
from llama_cpp import Llama
from urllib.parse import quote
from engine.tools import TOOLS, run_tool_logic
from engine.agents import AGENTS
from engine.engine import MiniTriniEngine
from backend.router import BackendRouter
from collections import Counter
from tkinterdnd2 import DND_FILES, TkinterDnD


print("LOADED FROM:", inspect.getfile(TriniVectorMemory))
print("METHODS:", dir(TriniVectorMemory))


print(TriniVectorMemory)
print(dir(TriniVectorMemory))

PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
# ======================================================================
#  BACKEND PROCESS (MAIN.PY)
# ======================================================================


# ======================================================================
#  LLAMA.CPP DETECTION
# ======================================================================
try:
    
    LLAMA_AVAILABLE = True
except Exception:
    LLAMA_AVAILABLE = False


# ======================================================================
#  THEME CONSTANTS
# ======================================================================
ACCENT = "#b347ff"
GLOW1  = "#b347ff"
GLOW2  = "#33eaff"
BG_MAIN = "#0f0014"
BG_PANEL = "#1a001f"
BG_TEXTBOX = "#120016"
TEXT_SOFT = "#d28cff"

MEMORY_DIR = PROJECT_ROOT / "AI_Core" / "chat_memory"
MODEL_DIR  = Path(__file__).resolve().parent / "AI_Core" / "Models"
RULES_FILE = Path("./AI_Core/TrinityMemoryBank/refusal_rules.json")



# ======================================================================
#  MINI TRINI APP — CLEAN, STRUCTURALLY RESTORED
# ======================================================================
class MiniTriniApp:

    def __init__(self, root):

        self.root = root
        root.title("🧠 MiniTrini v10.1 — Multi-Agent Trinity Console")
        root.configure(bg=BG_MAIN)
        root.geometry("1080x800")

        # backend
        self.backend_mode = "local"
        self.llm = None
        self.local_model_loaded = False
        self.llm_lock = threading.RLock()

        # runtime state
        self.memory = []
        self.memory_log = []
        self.active_tool = None
        self.active_agent = AGENTS[0]

        # executive protection
        self.executive_running = False

        # core state engine
        self.init_state_engine()

        # memory systems
        PROJECT_ROOT = Path(__file__).resolve().parent

        CHAT_MEMORY_DIR  = PROJECT_ROOT / "AI_Core" / "chat_memory"
        AGENT_MEMORY_DIR = PROJECT_ROOT / "AI_Core" / "Agent_training"
        TRAIN_MEMORY_DIR = PROJECT_ROOT / "AI_Core" / "TrinityMemoryBank" / "trained_memory"

        self.vector_memory = TriniVectorMemory(CHAT_MEMORY_DIR)
        self.agent_memory = TriniVectorMemory(AGENT_MEMORY_DIR)
        self.training_memory = TriniVectorMemory(TRAIN_MEMORY_DIR)

        # executive + router
        self.executive = TriniExecutive(PROJECT_ROOT)
        self.backend_router = BackendRouter(self)

       
        
        # ======================================================================
        # EXECUTIVE GOALS
       # ======================================================================

        active_goals = self.executive.get_active_goals()

        if active_goals:
            self.pipeline(f"Executive: {len(active_goals)} active goals detected.")


        # Backend state
        self.backend_mode = "local"
        self.llm = None
        self.local_model_loaded = False
        self.llm_lock = threading.RLock()
        
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

        
        self.init_state_engine()
        self.state["memory_items"] = 0
        self.state["tokens"] = 0
        self.state["pipeline"] = []

        self.state_set_agent(self.active_agent["name"])

        self.backend_process = None
        self.core_runtime_window = None        


        # UI
        self.build_ui()
        self.build_agents_panel()
        self.build_tools_panel()

        self.open_agents_panel()
        self.open_tools_panel()
        self.speed_profile = "build"  # default

        # devtools
        self.console_window = None
        self.console_box = None

        # SARA mode
        self.sara_mode = False
        self.sara_autopilot = False

        self.root.bind("<Control-Shift-S>", lambda e: self.canvas_save_last())
        self.root.bind("<Control-Shift-A>", lambda e: self.canvas_save_selection())
        self.root.bind("<Control-Shift-N>", lambda e: self.canvas_note_popup())
        root.title("🧠 MiniTrini v10.1 — Multi-Agent Trinity Console")
        root.configure(bg=BG_MAIN)
        root.geometry("1080x800")


    def detect_module_creation(self, text):
        t = text.lower()

        triggers = [
            "new project",
            "new module",
            "create module",
            "start module",
            "begin module",
            "working on module"
        ]

        if not any(k in t for k in triggers):
            return False

        # extract name (very simple first pass)
        words = text.replace('"', "").replace("'", "").split()

        skip = {
            "new","project","module","create",
            "start","begin","working","on"
        }

        name_parts = [w for w in words if w.lower() not in skip]

        if not name_parts:
            return False

        module_name = name_parts[0]

        self.state["active_module"] = module_name

        
        base = Path.home() / "MiniTrini_clean" / "AI_Core" / "trinity_canvas" / "modules"
        mod_dir = base / module_name
        mod_dir.mkdir(parents=True, exist_ok=True)
        
        # --- MODULE SCAFFOLD BOOTSTRAP ---
        (log_file := mod_dir / "project_log.jsonl").touch(exist_ok=True)

        (mod_dir / "notes").mkdir(exist_ok=True)
        (mod_dir / "memory").mkdir(exist_ok=True)
        (mod_dir / "build").mkdir(exist_ok=True)
        (mod_dir / "artifacts").mkdir(exist_ok=True)
        
        
        # ==================================================================
        # BLOCK: MODULE ENTRY FILE (main.py)
        # ==================================================================

        (mod_dir / "main.py").write_text(
            f"# {name} entry point\n\n"
            f'print("{name} module loaded")\n'
        )
        
       

        self.canvas_log(
            f"Module initialized: {module_name}",
            ["module_init"],
            "auto_intent"
        )

        print(f"[Canvas] active module → {module_name}")

        self.register_module(module_name)

        return True

        

    def canvas_log(self, data):
        project = self.state.get("active_module", "general")
        base = Path.home() / "MiniTrini_clean" / "AI_Core" / "trinity_canvas" / "modules"
        proj_dir = base / project

        proj_dir.mkdir(parents=True, exist_ok=True)

        log_file = proj_dir / "project_log.jsonl"

        entry = {
            "ts": datetime.now().isoformat(timespec="seconds"),
            **data
        }

        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, ensure_ascii=False) + "\n")

        
            
    def canvas_save_last(self):
        if not self.memory:
            return
        role, msg = self.memory[-1]
        if role == "assistant":
            self.canvas_log(msg, ["conversation"], "auto_last")
            
    def canvas_save_selection(self):
        try:
            sel = self.chat_text.get("sel.first", "sel.last")
            self.canvas_log(sel, ["selection"], "manual_select")
        except:
            pass
                        
    def canvas_note_popup(self):
        
        note = sd.askstring("Canvas Note", "Architect note:")
        if note:
            self.canvas_log(note, ["architect_note"], "manual_popup")
            

    REFINEMENT_DIRECTIVE = """
    Refine the following text for clarity, structure, and reasoning.

    Rules:
    • remove repetition
    • compress redundant ideas
    • strengthen logical structure
    • preserve the original meaning

    Return an improved version.
    """
    
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

        log_dir = Path(__file__).resolve().parent / "AI_Core" / "Executive"
        log_dir.mkdir(parents=True, exist_ok=True)

        with open(log_dir / "executive_log.jsonl", "a", encoding="utf-8") as f:
            f.write(json.dumps({
                "ts": timestamp,
                "event": event_type,
                "message": message
            }) + "\n")
                         
        
    def executive_tick(self):
        if not self.executive_running:
            try:
                active_goals = self.executive.get_active_goals()

                if active_goals:
                    self.pipeline("Executive tick")

                    threading.Thread(
                        target=self._run_chat_async,
                        args=("Executive check",),
                        daemon=True
                    ).start()

            except Exception as e:
                self.console_print(f"[EXECUTIVE TICK ERROR] {e}")

        self.root.after(20000, self.executive_tick)  # every 20s        
        


    def register_module(self, module_name):

        registry = Path.home() / "MiniTrini_clean" / "AI_Core" / "trinity_canvas" / "module_registry.json"

        print("[REGISTRY] called with:", module_name)
        print("[REGISTRY] file path:", registry)

        if registry.exists():
            print("[REGISTRY] registry exists — loading")
            with open(registry, "r", encoding="utf-8") as f:
                data = json.load(f)
        else:
            print("[REGISTRY] registry missing — creating new")
            data = {"modules": []}

        print("[REGISTRY] current modules:", [m["name"] for m in data["modules"]])

        for m in data["modules"]:
            if m["name"] == module_name:
                print("[REGISTRY] module already registered — skipping")
                return

        print("[REGISTRY] adding module:", module_name)

        data["modules"].append({
            "name": module_name,
            "created": datetime.now().isoformat(timespec="seconds"),
            "status": "active"
        })

        print("[REGISTRY] writing registry file...")

        with open(registry, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        print("[REGISTRY] write complete")    
            
              

        # --- SARA Mode State ---
        self.sara_mode = False          # User toggle (persistent)
        self.sara_autopilot = False     # Auto-activated (one-response)
        
        
        
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
        prompt = f"""
        You are distilling research knowledge for an AI learning system.

        Transform the following text into structured insight.

        Steps:
        1. Remove repetition
        2. Extract the core ideas
        3. Identify key principles
        4. Compress the information
        5. Preserve meaning

        Return a concise distilled version.

        TEXT:
        {model_input}

        DISTILLED:
        """
        

        with self.llm_lock:
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

    def build_session_bootstrap(self):
        return (
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
                
    def handle_file_drop(self, event):

        file_path = event.data.strip("{}")

        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            filename = os.path.basename(file_path)

            print("FILE DROPPED:", file_path)

            

            send_to_canvas(content, filename)
            

            

        except Exception as e:
            print("DROP ERROR:", e)               
                

    def open_canvas_with_content(self, filename, content):

        open_canvas(self, filename)

        send_to_canvas(
            f"# File: {filename}\n\n{content}"
        )



        if len(content) > 200000:
            content = content[:200000]   
            
        self.root.after(20000, self.executive_tick) 
    
 
                                  
    # ==================================================================
    #  UI BUILD
    # ==================================================================
    def build_ui(self):
        header = tk.Frame(self.root, bg=BG_MAIN)
        header.pack(fill="x", pady=8)
        
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

        tk.Button(
            input_frame,
            text="Send",
            bg=ACCENT,
            fg="black",
            font=("JetBrains Mono", 11, "bold"),
            command=self.send_message
        ).pack(side="left", padx=10)

        self.profile_button = tk.Button(
            self.root,
            text="Profile: BUILD",
            bg=ACCENT,
            fg="black",
            command=self._toggle_speed_profile
        )
        self.profile_button.pack(pady=6)
        
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
        self.root.bind("<Control-Shift-W>", lambda e: self.clear_session())
        
               
               
        
    # ==================================================================
    #  MESSAGE PIPELINE (NO DRIFT)
    # ==================================================================
    def send_message(self, event=None):
        text = self.input_box.get().strip()
        if not text:
            return

        self.output_box.insert("end", f"You: {text}\n")
        self.output_box.see("end")
        self.input_box.delete(0, "end")
        self.pipeline(f"User sent message")
        
        try:
            self.process_user_input(text)            
        except Exception as e:
            self.console_print(f"[MiniTrini ERROR] {e}")
            return

        if text.lower().startswith("goal:"):
            objective = text.replace("goal:", "").strip()
            goal = self.executive.add_goal(objective)

            self.log_executive_event("GOAL_CREATED", objective)

            if hasattr(self, "goal_text"):
                self.refresh_goal_dashboard()

            return

    def chat(self, sender, message):
        self.emit("chat", sender, message)

    def console(self, tag, message):
        self.emit("console", tag, message)            

    def process_user_input(self, text):
        self.memory.append(("User", text))
        
        # ==================================================================
        # BLOCK: HARD STOP COMMAND ROUTER
        # ==================================================================

        t = text.lower().strip()

        # --- create module ---
        if t.startswith("create module "):
            name = text.split("create module ",1)[1].strip()

            created = self.detect_module_creation(f"create module {name}")

            if created:
                self.register_module(name)
                self.state["active_module"] = name
                self.emit("chat","System",f"[Canvas] module registered → {name}")
                self.emit("chat","System",f"[Canvas] active module → {name}")
            else:
                self.emit("chat","System",f"[Canvas] failed to create module → {name}")

            return


        # ================================================================
        # BLOCK: OPEN MODULE (FIXED + TRACKING)
        # ================================================================

        if t.startswith("open module "):
            name = text.split("open module ",1)[1].strip()

            base = Path.home() / "MiniTrini_clean" / "AI_Core" / "trinity_canvas" / "modules"
            mod_dir = base / name

            if not mod_dir.exists():
                self.emit("chat", "System", f"[Canvas] module not found → {name}")
                return

            print(">>> OPEN MODULE START:", name)

            # SET MODULE (NO RESET YET)
            self.state["active_module"] = name
            self.state["project"] = name

            # ============================================================
            # RESUME (FIRST)
            # ============================================================
            state = self._resume_module_state(mod_dir, name)
            print(">>> RESUME RESULT:", state)

            if state and state.get("file"):
                file_path = mod_dir / Path(state["file"]).relative_to(name)

                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8", errors="ignore")

                    send_to_canvas(content, state["file"])
                    self.state["active_file"] = state["file"]

                    self.emit("chat","System",
                        f"[Canvas] resumed → {state['file']}"
                    )
                    return

            # ============================================================
            # RESET (ONLY AFTER RESUME FAILS)
            # ============================================================
            self.state["active_file"] = None
            self.state["current_task"] = None
            print(">>> STATE RESET")

            


            # 3️⃣ FALLBACK: ANY .py
            for root, dirs, files in os.walk(mod_dir):
                for f in sorted(files):
                    if f.endswith(".py"):
                        file_path = Path(root) / f
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        rel_path = file_path.relative_to(mod_dir)

                        send_to_canvas(content, f"{name}/{rel_path}")

                        self.state["active_file"] = f"{name}/{rel_path}"

                        self.canvas_log({
                            "event": "file_open",
                            "file": f"{name}/{rel_path}",
                            "module": name
                        })

                        self.emit("chat","System",
                            f"[Canvas] opened → {rel_path}"
                        )
                        return

            # ============================================================
            # FINAL FALLBACK
            # ============================================================
            log_file = mod_dir / "project_log.jsonl"
            if log_file.exists():
                content = log_file.read_text(encoding="utf-8", errors="ignore")

                send_to_canvas(content, f"{name}/project_log.jsonl")

                self.state["active_file"] = f"{name}/project_log.jsonl"

                self.emit("chat","System",
                    f"[Canvas] opened log → project_log.jsonl"
                )
        
        # =========================
        # OPEN MODULE FLOW
        # =========================

        print(">>> OPEN MODULE START:", name)

        # 1. HARD RESET FIRST
        self.state["active_file"] = None
        self.state["current_task"] = None
        print(">>> STATE RESET")

        # 2. SET MODULE
        self.state["active_module"] = name
        self.state["project"] = name

        # 3. RESUME
        state = self._resume_module_state(mod_dir, name)
        print(">>> RESUME RESULT:", state)

        if state and state.get("file"):
            self.state["active_file"] = state["file"]
            self._restore_active_file(mod_dir, name)

        # 4. AUTO DISCOVER (THIS WAS MISSING)
        print(">>> ENTER AUTO DISCOVER")

        if not self.state.get("active_file"):
            for root, dirs, files in os.walk(mod_dir):
                for f in files:
                    if f.endswith(".py"):
                        file_path = Path(root) / f

                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        rel_path = file_path.relative_to(mod_dir)

                        send_to_canvas(content, f"{name}/{rel_path}")
                        self.state["active_file"] = str(rel_path)
                        
                        self.state["active_file"] = f"{name}/{rel_path}"
                        
                        self.canvas_log({
                            "event": "file_open",
                            "file": f"{name}/{rel_path}",
                            "module": name
                        })

                        print(">>> AUTO OPENED:", rel_path)

                        self.emit("chat","System",
                            f"[Canvas] auto-opened → {rel_path}"
                        )
                        

        # 5. FINAL FALLBACK (ONLY IF NOTHING FOUND)
        if not self.state.get("active_file"):
            print(">>> FALLBACK → LOG")

            log_file = mod_dir / "project_log.jsonl"
            if log_file.exists():
                content = log_file.read_text(encoding="utf-8", errors="ignore")
                send_to_canvas(content, f"{name}/project_log.jsonl")
                
                self.state["active_file"] = f"{name}/{rel_path}"
                
                
        # ==================================================================
        # BLOCK: RESUME + RESTORE (CORRECT POSITION)
        # ==================================================================

        state = self._resume_module_state(mod_dir, name)

        resume_file = None
        if state and state.get("file"):
            resume_file = mod_dir / state["file"].replace(f"{name}/", "")

        # check if priority file exists
        priority_exists = (
            (mod_dir / "main.py").exists() or
            (mod_dir / "app.py").exists() or
            (mod_dir / "build" / "main.py").exists()
        )

        if resume_file and resume_file.exists() and not priority_exists:
            content = resume_file.read_text(encoding="utf-8", errors="ignore")

            send_to_canvas(content, state["file"])
            self.state["active_file"] = state["file"]

            self.emit("chat","System",
                f"[Canvas] resumed → {state['file']}"
            )
            return

        else:
            self.emit("chat","System",f"[Canvas] no prior state → {name}")
            
            

            try:
                # --- priority load order ---
                priority = [
                    mod_dir / "project_log.jsonl",
                    mod_dir / "notes",
                    mod_dir / "memory",
                    mod_dir / "build",
                    mod_dir / "artifacts",
                ]

                send_to_canvas(f"# MODULE: {name}\n")

                # 1️⃣ load project log FIRST (core context)
                log_file = mod_dir / "project_log.jsonl"
                if log_file.exists():
                    content = log_file.read_text(encoding="utf-8", errors="ignore")
                    send_to_canvas(content, f"{name}/project_log.jsonl")

                # 2️⃣ load structured folders (NOT raw dump)
                for folder in ["notes", "memory", "build", "artifacts"]:
                    fpath = mod_dir / folder
                    if fpath.exists():
                        send_to_canvas(f"\n# --- {folder.upper()} ---\n")

                        for file in sorted(fpath.glob("*"))[:5]:  # limit to avoid spam
                            if file.is_file():
                                content = file.read_text(encoding="utf-8", errors="ignore")
                                send_to_canvas(content, f"{name}/{folder}/{file.name}")

                self.emit("chat","System",f"[Canvas] opened module → {name}")

            except Exception as e:
                self.emit("chat","System",f"[Canvas ERROR] {e}")

       

        

            # ============================================================
            # PRIORITY FILE SEARCH (FIXED)
            # ============================================================
            priority_files = ["main.py", "app.py"]

            # 1️⃣ check root
            for fname in priority_files:
                file_path = mod_dir / fname
                if file_path.exists():
                    content = file_path.read_text(encoding="utf-8", errors="ignore")
                    rel_path = file_path.relative_to(mod_dir)

                    send_to_canvas(content, f"{name}/{rel_path}")

                    self.state["active_file"] = f"{name}/{rel_path}"

                    self.canvas_log({
                        "event": "file_open",
                        "file": f"{name}/{rel_path}",
                        "module": name
                    })

                    self.emit("chat","System",
                        f"[Canvas] opened → {rel_path}"
                    )
                    return


            # 2️⃣ check build/main.py
            build_dir = mod_dir / "build"

            if build_dir.exists():
                for fname in priority_files:
                    file_path = build_dir / fname
                    if file_path.exists():
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        rel_path = file_path.relative_to(mod_dir)

                        send_to_canvas(content, f"{name}/{rel_path}")

                        self.state["active_file"] = f"{name}/{rel_path}"

                        self.canvas_log({
                            "event": "file_open",
                            "file": f"{name}/{rel_path}",
                            "module": name
                        })

                        self.emit("chat","System",
                            f"[Canvas] opened → {rel_path}"
                        )
                        return

        print(">>> AUTO DISCOVER SKIPPED OR FAILED")
            
            
            
    # ==================================================================
    # BLOCK: ROUTER — LIST MODULES
    # ==================================================================
        if t == "list modules":
            self.list_modules()
            return   
            
            self.memory.append(("User", text))
            

        # --- MODULE INTENT LISTENER (safe insert) ---
       
        if self.detect_module_creation(text):
           print("MODULE DETECTOR:", text)
           return
    # ==================================================================
    # BLOCK: LIST MODULES FUNCTION
    # ==================================================================           
    def list_modules(self):

        registry = Path.home() / "MiniTrini_clean" / "AI_Core" / "trinity_canvas" / "module_registry.json"

        if not registry.exists():
            self.emit("chat", "System", "[Canvas] No modules registered.")
            return

        with open(registry, "r", encoding="utf-8") as f:
            data = json.load(f)

        modules = [m["name"] for m in data.get("modules", [])]

        if not modules:
            self.emit("chat", "System", "[Canvas] Registry empty.")
            return

        output = "\n".join(f"• {m}" for m in modules)
        self.emit("chat", "System", f"[Canvas Modules]\n{output}")           
               
               
    # ==================================================================
    # BLOCK: RESUME STATE FROM PROJECT LOG
    # ==================================================================
    def _resume_module_state(self, mod_dir, name):
        log_file = mod_dir / "project_log.jsonl"

        if not log_file.exists():
            return None

        try:
            lines = log_file.read_text(encoding="utf-8").splitlines()

            for line in reversed(lines):
                entry = json.loads(line)

                if entry.get("event") == "file_open":
                    return {
                        "file": entry.get("file")
                    }

        except Exception as e:
            print("[RESUME ERROR]", e)

        return None
 
 

        


        # ==================================================================
        # INSERT after state restore
        # ==================================================================
        if state:
            if state.get("file"):
                self.state["active_file"] = state["file"]
                self._restore_active_file(mod_dir, name)


    # ==================================================================
    # BLOCK: RESTORE FILE INTO CANVAS
    # ==================================================================
    def _restore_active_file(self, mod_dir, module_name):

        active_file = self.state.get("active_file")

        if not active_file:
            return

        target = mod_dir / active_file

        if not target.exists():
            self.console("SYSTEM", f"[RESTORE] file missing → {active_file}")
            return

        try:
            content = target.read_text(encoding="utf-8", errors="ignore")

            # send to canvas editor
            send_to_canvas(content, f"{module_name}/{active_file}")

            self.emit("chat","System",
                f"[Canvas] restored file → {active_file}"
            )

        except Exception as e:
            self.console("SYSTEM", f"[RESTORE ERROR] {e}")

                           
       

        self.state_set_task("Processing user input")
        self.activate_sara_autopilot("Trigger", text)
        self.start_thinking_animation()
        self.executive_running = False
        
    
        tool_name = self.state.get("tool")
        if tool_name:
            tool = next((t for t in TOOLS if t["name"] == tool_name), None)
            if tool and tool.get("intent") == "web_search":
                threading.Thread(target=self._run_web_search_async, args=(text,), daemon=True).start()
                return

        
        # Normal chat + non-web tools
        threading.Thread(
            target=self._run_chat_async,
            args=(text,),
            daemon=True
        ).start()
        
    def _run_chat_async(self, user_text: str):

        try:
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
            self.emit("chat", "Assistant", response_text)
            self.memory.append(("Assistant", response_text))
            self.clear_thinking()

        self.root.after(0, _ui_update)

        active_goals = self.executive.get_active_goals()
        
        if self.executive_running:
            return

            self.executive_running = True        

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

            decision = self.backend_router.send(check_prompt)

            if not decision:
                continue

            decision = decision.strip().upper()

            if "COMPLETE" in decision:
                self.executive.complete_goal(goal["id"])
                self.pipeline(f"Goal completed → {goal['id']}")
                self.emit("console", "GOAL_COMPLETED", goal["objective"])
                continue

            if "NO PROGRESS" not in decision:
                self.executive.update_goal(goal["id"], decision)

                if hasattr(self, "goal_text"):
                    self.refresh_goal_dashboard()

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
                    

                    def run_exec_step():
                        try:
                            result = self.autonomous_agent(next_step)
                            if result:
                                self.vector_memory.add_memory(str(result))
                        except Exception as e:
                            self.console_print(f"[EXECUTIVE ERROR] {e}")

                    threading.Thread(target=run_exec_step, daemon=True).start()

        if self.state.get("agent") == "Trini" and not response_text.startswith("[ERROR]"):
            self.vector_memory.add_memory(response_text)

        self.state["task"] = f"Running {self.state.get('agent')}/{self.state.get('tool')}"
        self.state["status"] = "Running"
        self.update_devtools()
        self.executive_running = False

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
        return user_text.strip()

        IDENTITY_BLOCK = (
            "You are Trini.\n"
            "Your name is Trini.\n"
            "Never invent alternate identities.\n"
            "If asked your name, answer: Trini.\n\n"
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

        header = (
            self.build_session_bootstrap() +
            IDENTITY_BLOCK +
            self.load_trini_memory_context() + "\n" +
            f"[Agent: {agent}]\n" +
            (f"[Tool: {tool['name']}]\n" if tool else "[Tool: None]\n") +
            TRINITY_TONE
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
            web_data = fetch_web_content(user_text)
            return f"Use this web data to answer:\n\n{web_data}\n\nQuestion:\n{user_text}" 
        if intent == "auto_research":
            results = self.autonomous_agent(user_text)
            return f"Autonomous research results:\n\n{results}"                       

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

        btn_frame = tk.Frame(self.training_win, bg=BG_PANEL)
        btn_frame.pack(fill="x")

        tk.Button(
            btn_frame,
            text="Start Recursive Training",
            bg=ACCENT,
            fg="black",
            font=("JetBrains Mono", 12, "bold"),
            relief="ridge",
            command=self.run_recursive_training
        ).pack(pady=10)


    def run_recursive_training(self):

        print("RUN RECURSIVE TRAINING TRIGGERED")

        seed = self.get_last_assistant_message()
        print("SEED =", repr(seed))

        if not seed:
            print("NO SEED TEXT — STOP")
            return

        engine = RecursiveLearningEngine(self)

        print("ENGINE CREATED")

        def run_engine():
            try:
                result = engine.start(seed)
                self.root.after(0, lambda: self._display_training(engine, result))
            except Exception as e:
                self.root.after(0, lambda err=e: self.train_logs.insert("end", f"Error: {err}\n"))

        threading.Thread(target=run_engine, daemon=True).start()
                
            
        def run_engine():
            try:
                result = engine.start(seed)
                self.root.after(0, lambda: self._display_training(engine, result))
            except Exception as e:
                err_msg = f"Error: {e}\n"
                self.root.after(0, lambda msg=err_msg: self.train_logs.insert("end", msg))
                               

        run_engine()
        
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
        url = f"https://duckduckgo.com/html/?q={quote(query)}"
        headers = {"User-Agent": "Mozilla/5.0"}
        res = requests.get(url, headers=headers, timeout=(5, 10))
        soup = BeautifulSoup(res.text, "html.parser")

        results = []
        for result in soup.select(".result")[:max_results]:
            link = result.select_one(".result__a")
            snippet = result.select_one(".result__snippet")
            if link:
                results.append({
                    "title": link.get_text(),
                    "url": link["href"],
                    "snippet": snippet.get_text() if snippet else ""
                })
        return results

    
        
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

            summary = self.backend_router.send(summary_prompt)

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
        
        if self.app.llm:        
            self.app.llm.reset()

    def start(self, text):
        self.active = True
        self.current_cycle = 0
        refined = text.strip()
        
        improved = ""

        self.logs.append(
            f"[cycle {self.current_cycle + 1}]\n"
            f"Input:\n{refined[:1500]}\n\n"
            f"Output:\n{improved}\n"
        )

        while self.active and self.current_cycle < self.max_cycles:

            print("RECURSIVE LOOP START")
            print("cycle =", self.current_cycle)

            model_input = refined[-1500:]

            print("MODEL INPUT LEN =", len(model_input))

            improved = self.app.process_training_pass(model_input)

            print("RAW MODEL OUTPUT =", repr(improved))

            if not improved:
                print("TRAINING STOP: no output from model")
                break

            improved = improved.strip()
            
            if len(improved) >= len(refined):
                print("TRAINING STOP: no compression improvement")
                break

            print("IMPROVED LEN =", len(improved))

            if len(improved) > 50 and len(set(improved)) < 10:
                print("TRAINING STOP: degenerate output")
                self.logs.append("[WARNING] Degenerate output detected.")
                break

            if len(improved) > 80:
                try:
                    print("TRAINING MEMORY SAVE ATTEMPT")
                    self.app.training_memory.add_memory(improved)
                except Exception as e:
                    print("TRAINING MEMORY ERROR:", e)

            self.logs.append(
                f"[cycle {self.current_cycle + 1}]\n"
                f"Input:\n{refined[:1500]}\n\n"
                f"Output:\n{improved}\n"
            )

            refined = improved
            self.current_cycle += 1

            print("CYCLE COMPLETE")

            time.sleep(0.6)

        
        self.active = False
        return refined
        



# ======================================================================
#  MAIN EXECUTION
# ======================================================================
if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app  = MiniTriniApp(root)

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