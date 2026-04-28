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
try:
    model = SentenceTransformer("all-MiniLM-L6-v2")
except Exception as e:
    print("SentenceTransformer load failed:", e)
    model = None
from AI_Core.TrinityMemoryBank.trini_vector_memory import TriniVectorMemory
import inspect
from AI_Core.Executive.trini_executive import TriniExecutive
from TrinityCanvas import  send_to_canvas 
from bs4 import BeautifulSoup
try:
    from llama_cpp import Llama
except Exception as e:
    Llama = None
    print("llama_cpp import failed:", e)
from urllib.parse import quote
from engine.tools import TOOLS, run_tool_logic
from engine.agents import AGENTS
from engine.engine import MiniTriniEngine
from backend.router import BackendRouter
from collections import Counter


LLAMA_AVAILABLE = Llama is not None

BG = "#0a0f1c"
FG = "#00ffff"
ACCENT = "#ff00ff"

# =========================
# Tool Definitions
# =========================
TOOLS = {
    "browser": {
        "desc": "Open a URL and summarize the contents.",
        "fn": lambda self, url: self.open_browser_tool(url)
    },
    "wiki": {
        "desc": "Search Wikipedia for a term and summarize it.",
        "fn": lambda self, query: self.wikipedia_tool(query)
    },
    "calculator": {
        "desc": "Evaluate a math expression.",
        "fn": lambda self, expr: self.calculator_tool(expr)
    },
    "memory_search": {
        "desc": "Search Trinity's vector memory for relevant context.",
        "fn": lambda self, q: self.search_memory(q)
    },
}


# =========================
# Agent Definitions
# =========================
AGENTS = {
    "Researcher": {
        "role": "Finds facts, references, and research insights.",
        "style": "analytical"
    },
    "Planner": {
        "role": "Creates structured plans and next steps.",
        "style": "strategic"
    },
    "Writer": {
        "role": "Turns ideas into polished text.",
        "style": "creative"
    },
    "Critic": {
        "role": "Finds flaws, weak points, and improvements.",
        "style": "skeptical"
    }
}


def safe_json_load(path, default):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def safe_json_save(path, data):
    try:
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    except Exception as e:
        print("JSON SAVE ERROR:", e)


def ensure_executable(p):
    try:
        mode = os.stat(p).st_mode
        os.chmod(p, mode | stat.S_IEXEC)
    except Exception:
        pass


class TrinityCanvas:
    def __init__(self):
        self.entries = []

    def push(self, kind, content, meta=None):
        item = {
            "time": datetime.now().strftime("%H:%M:%S"),
            "kind": kind,
            "content": content,
            "meta": meta or {}
        }
        self.entries.append(item)

    def export(self):
        return list(self.entries)


class PulseOrb(tk.Canvas):
    def __init__(self, master, x=120, y=120, r=36, **kw):
        super().__init__(master, width=240, height=240, bg=BG, highlightthickness=0, **kw)
        self.cx, self.cy, self.r = x, y, r
        self.phase = 0.0
        self.glow = self.create_oval(x-r, y-r, x+r, y+r, fill=ACCENT, outline="")
        self.core = self.create_oval(x-r+10, y-r+10, x+r-10, y+r-10, fill=FG, outline="")
        self.text = self.create_text(x, y+70, text="TRINITY", fill=FG, font=("JetBrains Mono", 11, "bold"))
        self.animate()

    def animate(self):
        self.phase += 0.12
        pulse = 10 + 5 * math.sin(self.phase)
        alpha_r = self.r + pulse
        self.coords(self.glow, self.cx-alpha_r, self.cy-alpha_r, self.cx+alpha_r, self.cy+alpha_r)
        self.after(50, self.animate)


class MiniTriniV10:
    def __init__(self, root):
        self.root = root
        self.root.title("MiniTrini v10.1 — Trinity Multi-Agent")
        self.root.configure(bg=BG)
        self.root.geometry("1280x900")

        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        self.memory_path = os.path.join(self.base_dir, "memory", "memory.json")
        self.canvas_path = os.path.join(self.base_dir, "memory", "canvas.json")
        self.config_path = os.path.join(self.base_dir, "config", "settings.json")
        self.module_dir = os.path.join(self.base_dir, "modules")
        self.local_model_dir = os.path.join(self.base_dir, "AI_Core", "Models")
        
        print("LOCAL MODEL DIR =", self.local_model_dir)
        os.makedirs(os.path.dirname(self.memory_path), exist_ok=True)
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        os.makedirs(self.module_dir, exist_ok=True)
        os.makedirs(self.local_model_dir, exist_ok=True)

        self.memory = safe_json_load(self.memory_path, [])
        self.canvas = TrinityCanvas()
        self.saved_canvas = safe_json_load(self.canvas_path, [])
        for item in self.saved_canvas:
            try:
                self.canvas.entries.append(item)
            except Exception:
                pass

        self.settings = safe_json_load(self.config_path, {
            "backend_mode": "ollama",
            "ollama_model": "llama3",
            "temperature": 0.7,
            "top_p": 0.95,
            "max_tokens": 512
        })

        self.backend_mode = self.settings.get("backend_mode", "ollama")
        self.ollama_model = self.settings.get("ollama_model", "llama3")
        self.temperature = self.settings.get("temperature", 0.7)
        self.top_p = self.settings.get("top_p", 0.95)
        self.max_tokens = self.settings.get("max_tokens", 512)

        self.vector_memory = None
        try:
            self.vector_memory = TriniVectorMemory()
        except Exception as e:
            print("Vector memory init failed:", e)
            self.vector_memory = None

        self.executive = None
        try:
            self.executive = TriniExecutive(self)
        except Exception as e:
            print("Executive init failed:", e)

        self.engine = None
        try:
            self.engine = MiniTriniEngine(self)
        except Exception as e:
            print("Engine init failed:", e)

        self.backend_router = BackendRouter(self)

        self.llm = None
        self.local_model_loaded = False
        self.llm_lock = threading.Lock()

        self.voice_enabled = False
        self.wake_phrase = "trinity"
        self.auto_tool_mode = True
        self.thinking = False
        self.current_task = None
        self.stop_requested = False

        self._build_ui()
        self._render_saved_canvas()
        self.refresh_memory_list()

    def _build_ui(self):
        top = tk.Frame(self.root, bg=BG)
        top.pack(fill="x", padx=10, pady=8)

        self.orb = PulseOrb(top)
        self.orb.pack(side="left", padx=10)

        controls = tk.Frame(top, bg=BG)
        controls.pack(side="left", fill="both", expand=True, padx=10)

        title = tk.Label(
            controls,
            text="MiniTrini v10.1 — Trinity Multi-Agent Edition",
            fg=FG,
            bg=BG,
            font=("JetBrains Mono", 18, "bold")
        )
        title.pack(anchor="w", pady=(6, 10))

        row1 = tk.Frame(controls, bg=BG)
        row1.pack(fill="x", pady=4)

        tk.Label(row1, text="Backend:", fg=FG, bg=BG, font=("JetBrains Mono", 11)).pack(side="left")
        self.backend_label = tk.Label(
            row1,
            text=self.backend_mode.upper(),
            fg=ACCENT,
            bg=BG,
            font=("JetBrains Mono", 11, "bold")
        )
        self.backend_label.pack(side="left", padx=8)

        tk.Label(row1, text="Local Model:", fg=FG, bg=BG, font=("JetBrains Mono", 11)).pack(side="left", padx=(20, 4))
        self.model_var = tk.StringVar()
        self.model_menu = ttk.Combobox(row1, textvariable=self.model_var, width=42)
        self.model_menu.pack(side="left", padx=4)
        self.model_menu["values"] = self.get_model_list()

        tk.Button(
            row1, text="Reload Models", command=self.reload_models,
            bg=ACCENT, fg="black", font=("JetBrains Mono", 10, "bold")
        ).pack(side="left", padx=6)

        tk.Button(
            row1, text="Load Selected", command=self.load_local_model,
            bg=FG, fg="black", font=("JetBrains Mono", 10, "bold")
        ).pack(side="left", padx=6)

        row2 = tk.Frame(controls, bg=BG)
        row2.pack(fill="x", pady=4)

        tk.Label(row2, text="Temperature", fg=FG, bg=BG, font=("JetBrains Mono", 10)).pack(side="left")
        self.temp_scale = tk.Scale(
            row2, from_=0.1, to=1.5, resolution=0.05, orient="horizontal",
            bg=BG, fg=FG, troughcolor="#13233f", highlightthickness=0,
            length=180
        )
        self.temp_scale.set(self.temperature)
        self.temp_scale.pack(side="left", padx=6)

        tk.Label(row2, text="Top P", fg=FG, bg=BG, font=("JetBrains Mono", 10)).pack(side="left", padx=(18, 0))
        self.topp_scale = tk.Scale(
            row2, from_=0.1, to=1.0, resolution=0.05, orient="horizontal",
            bg=BG, fg=FG, troughcolor="#13233f", highlightthickness=0,
            length=180
        )
        self.topp_scale.set(self.top_p)
        self.topp_scale.pack(side="left", padx=6)

        tk.Label(row2, text="Max Tokens", fg=FG, bg=BG, font=("JetBrains Mono", 10)).pack(side="left", padx=(18, 0))
        self.max_tokens_var = tk.StringVar(value=str(self.max_tokens))
        tk.Entry(row2, textvariable=self.max_tokens_var, width=8, bg="#111827", fg=FG, insertbackground=FG).pack(side="left", padx=6)

        tk.Button(
            row2, text="Save Settings", command=self.save_settings,
            bg=ACCENT, fg="black", font=("JetBrains Mono", 10, "bold")
        ).pack(side="left", padx=10)

        middle = tk.PanedWindow(self.root, orient="horizontal", sashrelief="raised", bg=BG)
        middle.pack(fill="both", expand=True, padx=10, pady=6)

        left = tk.Frame(middle, bg=BG)
        center = tk.Frame(middle, bg=BG)
        right = tk.Frame(middle, bg=BG)
        middle.add(left, minsize=280)
        middle.add(center, minsize=520)
        middle.add(right, minsize=280)

        tk.Label(left, text="Memory / Modules", fg=FG, bg=BG, font=("JetBrains Mono", 12, "bold")).pack(anchor="w")
        self.memory_list = tk.Listbox(left, bg="#08111f", fg=FG, selectbackground=ACCENT, width=36, height=28)
        self.memory_list.pack(fill="both", expand=True, pady=6)

        mem_buttons = tk.Frame(left, bg=BG)
        mem_buttons.pack(fill="x", pady=4)
        tk.Button(mem_buttons, text="Search Memory", command=self.memory_search_prompt, bg=ACCENT, fg="black").pack(side="left", padx=3)
        tk.Button(mem_buttons, text="Train Memory", command=self.train_memory_prompt, bg=FG, fg="black").pack(side="left", padx=3)
        tk.Button(mem_buttons, text="Create Module", command=self.create_module_prompt, bg=ACCENT, fg="black").pack(side="left", padx=3)

        tk.Label(center, text="Trinity Chat", fg=FG, bg=BG, font=("JetBrains Mono", 12, "bold")).pack(anchor="w")
        self.chat = scrolledtext.ScrolledText(center, bg="#08111f", fg=FG, insertbackground=FG, wrap="word", font=("Consolas", 11))
        self.chat.pack(fill="both", expand=True, pady=6)
        self.chat.tag_config("user", foreground="#7dd3fc")
        self.chat.tag_config("ai", foreground="#a7f3d0")
        self.chat.tag_config("system", foreground="#f9a8d4")
        self.chat.tag_config("tool", foreground="#fde68a")
        self.chat.tag_config("agent", foreground="#c4b5fd")

        entry_row = tk.Frame(center, bg=BG)
        entry_row.pack(fill="x", pady=6)
        self.entry = tk.Entry(entry_row, bg="#111827", fg=FG, insertbackground=FG, font=("Consolas", 12))
        self.entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.entry.bind("<Return>", lambda e: self.send_chat())

        tk.Button(entry_row, text="Send", command=self.send_chat, bg=FG, fg="black", font=("JetBrains Mono", 10, "bold")).pack(side="left", padx=3)
        tk.Button(entry_row, text="Stop", command=self.request_stop, bg=ACCENT, fg="black", font=("JetBrains Mono", 10, "bold")).pack(side="left", padx=3)
        tk.Button(entry_row, text="Voice", command=self.toggle_voice, bg=ACCENT, fg="black", font=("JetBrains Mono", 10, "bold")).pack(side="left", padx=3)
        tk.Button(entry_row, text="Run Tools", command=self.tool_prompt, bg=FG, fg="black", font=("JetBrains Mono", 10, "bold")).pack(side="left", padx=3)

        tk.Label(right, text="Canvas / Agents", fg=FG, bg=BG, font=("JetBrains Mono", 12, "bold")).pack(anchor="w")
        self.canvas_view = scrolledtext.ScrolledText(right, bg="#08111f", fg=FG, wrap="word", font=("Consolas", 10))
        self.canvas_view.pack(fill="both", expand=True, pady=6)

        right_buttons = tk.Frame(right, bg=BG)
        right_buttons.pack(fill="x", pady=4)
        tk.Button(right_buttons, text="Clear Canvas", command=self.clear_canvas, bg=ACCENT, fg="black").pack(side="left", padx=3)
        tk.Button(right_buttons, text="Run Agents", command=self.run_agents_prompt, bg=FG, fg="black").pack(side="left", padx=3)
        tk.Button(right_buttons, text="Export Canvas", command=self.export_canvas, bg=ACCENT, fg="black").pack(side="left", padx=3)

        bottom = tk.Frame(self.root, bg=BG)
        bottom.pack(fill="x", padx=10, pady=(0, 10))

        self.status = tk.Label(
            bottom,
            text="Ready.",
            fg=FG,
            bg=BG,
            anchor="w",
            font=("JetBrains Mono", 10)
        )
        self.status.pack(fill="x")

    def set_status(self, text):
        self.status.config(text=text)
        self.root.update_idletasks()

    def emit(self, channel, speaker, text):
        tag = "system"
        if channel == "user":
            tag = "user"
        elif channel == "ai":
            tag = "ai"
        elif channel == "tool":
            tag = "tool"
        elif channel == "agent":
            tag = "agent"

        self.chat.insert("end", f"{speaker}: {text}\n\n", tag)
        self.chat.see("end")
        self.root.update_idletasks()

    def save_settings(self):
        try:
            self.temperature = float(self.temp_scale.get())
            self.top_p = float(self.topp_scale.get())
            self.max_tokens = int(self.max_tokens_var.get().strip())
        except Exception:
            self.emit("system", "System", "Invalid generation setting values.")
            return

        self.settings["backend_mode"] = self.backend_mode
        self.settings["ollama_model"] = self.ollama_model
        self.settings["temperature"] = self.temperature
        self.settings["top_p"] = self.top_p
        self.settings["max_tokens"] = self.max_tokens
        safe_json_save(self.config_path, self.settings)
        self.emit("system", "System", "Settings saved.")

    def get_model_list(self):
        try:
            print("MODEL DIR:", self.local_model_dir)
            print("DIR EXISTS:", os.path.exists(self.local_model_dir))
            print("DIR CONTENTS:", os.listdir(self.local_model_dir) if os.path.exists(self.local_model_dir) else [])

            files = []
            for f in os.listdir(self.local_model_dir):
                if f.lower().endswith(".gguf"):
                    files.append(f)

            files.sort()
            return files
        except Exception as e:
            print("MODEL LIST ERROR:", e)
            return []

    def reload_models(self):
        self.model_menu["values"] = self.get_model_list()
        self.emit("system", "System", "Model list reloaded.")

    def detect_chat_format(self, model_name):
        name = model_name.lower()
        if "mistral" in name:
            return "mistral-instruct"
        if "phi" in name:
            return "chatml"
        if "zephyr" in name:
            return "chatml"
        if "openchat" in name:
            return "chatml"
        if "qwen" in name:
            return "chatml"
        if "deepseek" in name:
            return "chatml"
        if "gemma" in name:
            return "chatml"
        if "llama-3" in name or "llama3" in name:
            return "llama-3"
        if "llama-2" in name or "llama2" in name:
            return "llama-2"
        if "vicuna" in name:
            return "vicuna"
        if "alpaca" in name:
            return "alpaca"
        return "chatml"

    def load_local_model(self, event=None):
        model_name = self.model_var.get().strip()
        if not model_name:
            self.emit("system", "System", "No local model selected.")
            return

        if not LLAMA_AVAILABLE:
            self.emit("system", "System", "llama_cpp is not available.")
            return

        model_path = os.path.join(self.local_model_dir, model_name)
        if not os.path.exists(model_path):
            self.emit("system", "System", f"Model file not found: {model_path}")
            return

        self.set_status(f"Loading local model: {model_name}")

        try:
            self.llm = None

            chat_format = None
            lower = model_name.lower()

            if "mistral" in lower:
                chat_format = "mistral-instruct"
            elif "llama-3" in lower or "llama3" in lower:
                chat_format = "llama-3"
            elif "llama-2" in lower or "llama2" in lower:
                chat_format = "llama-2"
            elif "vicuna" in lower:
                chat_format = "vicuna"
            elif "alpaca" in lower:
                chat_format = "alpaca"

            self.llm = Llama(
                model_path=model_path,
                n_ctx=2048,
                n_threads=4,
                n_batch=256,
                n_gpu_layers=0,
                use_mmap=True,
                use_mlock=False,
                verbose=True,
                chat_format=chat_format
            )

            self.local_model_loaded = True
            self.emit("system", "System", f"Loaded local model: {model_name}")

        except Exception as e:
            self.llm = None
            self.local_model_loaded = False
            self.emit("system", "System", f"[MODEL LOAD ERROR] {e}")
            print("MODEL LOAD ERROR:", e)

        finally:
            self.set_status("Ready.")

    def toggle_backend(self):
        self.backend_mode = "local" if self.backend_mode == "ollama" else "ollama"
        self.backend_label.config(text=self.backend_mode.upper())
        self.emit("system", "System", f"Backend switched to: {self.backend_mode}")
        self.save_settings()

    def request_stop(self):
        self.stop_requested = True
        self.emit("system", "System", "Stop requested.")

    def toggle_voice(self):
        self.voice_enabled = not self.voice_enabled
        state = "enabled" if self.voice_enabled else "disabled"
        self.emit("system", "System", f"Voice {state}.")

    def _render_saved_canvas(self):
        self.canvas_view.delete("1.0", "end")
        for item in self.canvas.entries:
            self.canvas_log(item)

    def canvas_log(self, *args):
        if len(args) == 1 and isinstance(args[0], dict):
            item = args[0]
            t = item.get("time", datetime.now().strftime("%H:%M:%S"))
            kind = item.get("kind", "info")
            content = item.get("content", "")
        elif len(args) >= 3:
            kind, speaker, content = args[:3]
            t = datetime.now().strftime("%H:%M:%S")
            content = f"{speaker}: {content}"
        else:
            t = datetime.now().strftime("%H:%M:%S")
            kind = "info"
            content = str(args[0]) if args else ""

        self.canvas.push(kind, content)
        self.canvas_view.insert("end", f"[{t}] {kind.upper()} :: {content}\n\n")
        self.canvas_view.see("end")
        safe_json_save(self.canvas_path, self.canvas.export())

    def clear_canvas(self):
        self.canvas.entries = []
        self.canvas_view.delete("1.0", "end")
        safe_json_save(self.canvas_path, [])
        self.emit("system", "System", "Canvas cleared.")

    def export_canvas(self):
        path = os.path.join(self.base_dir, "memory", f"canvas_export_{int(time.time())}.json")
        safe_json_save(path, self.canvas.export())
        self.emit("system", "System", f"Canvas exported to {path}")

    def refresh_memory_list(self):
        self.memory_list.delete(0, "end")
        for i, item in enumerate(self.memory):
            text = item.get("text", "")
            preview = text[:80].replace("\n", " ")
            self.memory_list.insert("end", f"{i+1}. {preview}")

        try:
            module_files = [f for f in os.listdir(self.module_dir) if f.endswith(".py")]
            for mf in sorted(module_files):
                self.memory_list.insert("end", f"[MODULE] {mf}")
        except Exception:
            pass

    def add_memory(self, text, meta=None):
        item = {
            "time": datetime.now().isoformat(),
            "text": text,
            "meta": meta or {}
        }
        self.memory.append(item)
        safe_json_save(self.memory_path, self.memory)
        self.refresh_memory_list()
        try:
            if self.vector_memory is not None:
                self.vector_memory.add_memory(text, metadata=meta or {})
        except Exception as e:
            print("Vector add failed:", e)

    def search_memory(self, query):
        hits = []

        try:
            q = query.lower()
            for item in self.memory:
                text = item.get("text", "")
                if q in text.lower():
                    hits.append(text)
        except Exception:
            pass

        try:
            if self.vector_memory is not None:
                vec_hits = self.vector_memory.search(query, top_k=5)
                for h in vec_hits:
                    if isinstance(h, dict):
                        text = h.get("text") or h.get("content") or str(h)
                    else:
                        text = str(h)
                    if text not in hits:
                        hits.append(text)
        except Exception as e:
            print("Vector search failed:", e)

        return hits[:8]

    def memory_search_prompt(self):
        q = sd.askstring("Search Memory", "Enter memory query:")
        if not q:
            return
        results = self.search_memory(q)
        if not results:
            self.emit("system", "System", "No memory hits.")
            return
        self.emit("tool", "Memory", "\n---\n".join(results[:5]))

    def train_memory_prompt(self):
        text = sd.askstring("Train Memory", "Paste text to distill into memory:")
        if not text:
            return
        self.emit("system", "System", "Training memory...")
        threading.Thread(target=self._train_memory_worker, args=(text,), daemon=True).start()

    def _train_memory_worker(self, text):
        try:
            distilled = self.process_training_pass(text)
            self.add_memory(distilled, {"source": "training_pass"})
            self.emit("ai", "Trinity", distilled)
            self.canvas_log("memory", "Trainer", distilled)
        except Exception as e:
            self.emit("system", "System", f"Training failed: {e}")

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
{text}

DISTILLED:
"""
        with self.llm_lock:
            result = self.backend_router.send(prompt)
        return result.strip()

    def create_module_prompt(self):
        name = sd.askstring("Create Module", "Module name:")
        if not name:
            return
        goal = sd.askstring("Create Module", "What should this module do?")
        if not goal:
            return
        threading.Thread(target=self._create_module_worker, args=(name, goal), daemon=True).start()

    def _create_module_worker(self, module_name, goal):
        try:
            self.emit("system", "System", f"Creating module '{module_name}' ...")
            prompt = f"""
You are writing a Python module for the Trinity system.

Create a single Python module named {module_name}.
Goal: {goal}

Requirements:
- Clean Python
- Safe defaults
- Include a callable main function if appropriate
- Avoid external dependencies unless necessary

Return only Python code.
"""
            code = self.backend_router.send(prompt)
            code = self.extract_code_block(code)
            if not code.strip():
                raise RuntimeError("Model returned empty module code.")

            path = os.path.join(self.module_dir, f"{module_name}.py")
            with open(path, "w", encoding="utf-8") as f:
                f.write(code)

            self.emit("system", "System", f"Module created: {path}")
            self.canvas_log("module", "Builder", f"Created module {module_name}")
            self.refresh_memory_list()
        except Exception as e:
            self.emit("system", "System", f"Module creation failed: {e}")

    def extract_code_block(self, text):
        m = re.findall(r"```(?:python)?\s*(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if m:
            return m[0].strip()
        return text.strip()

    def wikipedia_tool(self, query):
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{quote(query)}"
            r = requests.get(url, timeout=12)
            if r.status_code != 200:
                return f"Wikipedia lookup failed ({r.status_code})."
            data = r.json()
            return data.get("extract", "No summary found.")
        except Exception as e:
            return f"Wikipedia error: {e}"

    def calculator_tool(self, expr):
        try:
            if not re.fullmatch(r"[0-9\.\+\-\*\/\(\)\s%]+", expr):
                return "Unsafe expression."
            return str(eval(expr, {"__builtins__": {}}, {}))
        except Exception as e:
            return f"Calculator error: {e}"

    def open_browser_tool(self, url):
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            r = requests.get(url, timeout=15, headers=headers)
            soup = BeautifulSoup(r.text, "html.parser")
            text = " ".join(t.get_text(" ", strip=True) for t in soup.find_all(["p", "h1", "h2", "h3", "li"]))
            text = re.sub(r"\s+", " ", text).strip()
            if not text:
                return "No readable content found."
            snippet = text[:6000]
            prompt = f"Summarize the following webpage clearly and concisely:\n\n{snippet}"
            return self.backend_router.send(prompt)
        except Exception as e:
            return f"Browser tool error: {e}"

    def tool_prompt(self):
        name = sd.askstring("Run Tool", f"Available tools: {', '.join(TOOLS.keys())}\n\nEnter tool name:")
        if not name:
            return
        name = name.strip()
        if name not in TOOLS:
            self.emit("system", "System", f"Unknown tool: {name}")
            return
        arg = sd.askstring("Run Tool", f"Enter argument for {name}:")
        if arg is None:
            return
        threading.Thread(target=self._tool_worker, args=(name, arg), daemon=True).start()

    def _tool_worker(self, tool_name, arg):
        self.emit("tool", "Tool", f"Running {tool_name}({arg})")
        try:
            result = TOOLS[tool_name]["fn"](self, arg)
        except Exception as e:
            try:
                result = run_tool_logic(self, tool_name, arg)
            except Exception:
                result = f"Tool failed: {e}"

        self.emit("tool", tool_name, str(result))
        self.canvas_log("tool", tool_name, str(result))
        self.add_memory(f"[TOOL:{tool_name}] {arg} -> {result}", {"tool": tool_name, "arg": arg})

    def run_agents_prompt(self):
        task = sd.askstring("Run Agents", "Enter the task for the Trinity agents:")
        if not task:
            return
        threading.Thread(target=self.run_multi_agent, args=(task,), daemon=True).start()

    def run_multi_agent(self, task):
        self.emit("system", "System", f"Running agents on task: {task}")
        self.canvas_log("task", "System", task)
        outputs = {}
        for name, info in AGENTS.items():
            if self.stop_requested:
                self.stop_requested = False
                self.emit("system", "System", "Agent run stopped.")
                return

            prompt = f"""
You are the {name} agent in a Trinity multi-agent system.

Role:
{info['role']}

Style:
{info['style']}

Task:
{task}

Give your best contribution for this task.
"""
            try:
                out = self.backend_router.send(prompt)
            except Exception as e:
                out = f"{name} failed: {e}"
            outputs[name] = out
            self.emit("agent", name, out)
            self.canvas_log("agent", name, out)

        synthesis_prompt = f"""
You are Trinity, synthesizing the outputs of several specialist agents.

TASK:
{task}

AGENT OUTPUTS:
{json.dumps(outputs, indent=2)}

Create a final integrated answer.
"""
        final = self.backend_router.send(synthesis_prompt)
        self.emit("ai", "Trinity", final)
        self.canvas_log("synthesis", "Trinity", final)
        self.add_memory(final, {"source": "multi_agent", "task": task})

    def build_context(self, latest_user_msg):
        recent = self.memory[-10:]
        memory_text = "\n".join([f"- {m.get('text', '')[:500]}" for m in recent])
        canvas_text = "\n".join([f"- {c.get('content', '')[:400]}" for c in self.canvas.entries[-8:]])

        hits = self.search_memory(latest_user_msg)
        hit_text = "\n".join([f"- {h[:500]}" for h in hits[:5]])

        return f"""
You are Trinity, a multi-agent AI assistant with memory and tools.

Recent Memory:
{memory_text}

Relevant Memory:
{hit_text}

Recent Canvas:
{canvas_text}

User Message:
{latest_user_msg}
"""

    def decide_tools(self, user_msg):
        msg = user_msg.lower().strip()
        tool_calls = []

        if re.search(r"https?://", msg):
            urls = re.findall(r"https?://\S+", user_msg)
            for url in urls:
                tool_calls.append(("browser", url))

        if msg.startswith("wiki ") or msg.startswith("wikipedia "):
            q = user_msg.split(" ", 1)[1].strip()
            tool_calls.append(("wiki", q))

        if msg.startswith("calc ") or msg.startswith("calculate "):
            q = user_msg.split(" ", 1)[1].strip()
            tool_calls.append(("calculator", q))

        if "search memory" in msg or msg.startswith("memory "):
            q = user_msg.replace("search memory", "").replace("memory", "").strip()
            if q:
                tool_calls.append(("memory_search", q))

        return tool_calls

    def send_chat(self):
        user_msg = self.entry.get().strip()
        if not user_msg:
            return
        self.entry.delete(0, "end")
        self.emit("user", "You", user_msg)
        self.add_memory(user_msg, {"speaker": "user"})
        threading.Thread(target=self._chat_worker, args=(user_msg,), daemon=True).start()

    def _chat_worker(self, user_msg):
        self.thinking = True
        self.set_status("Thinking...")
        try:
            tool_results = []
            if self.auto_tool_mode:
                for tool_name, arg in self.decide_tools(user_msg):
                    try:
                        self.emit("tool", "Tool", f"Auto-running {tool_name}({arg})")
                        result = TOOLS[tool_name]["fn"](self, arg)
                        tool_results.append((tool_name, arg, result))
                        self.canvas_log("tool", tool_name, str(result))
                    except Exception as e:
                        tool_results.append((tool_name, arg, f"Tool error: {e}"))

            tool_context = "\n".join([f"{n}({a}) => {r}" for n, a, r in tool_results])

            context = self.build_context(user_msg)
            prompt = f"""
{context}

Tool Results:
{tool_context}

Respond helpfully, clearly, and with good reasoning.
"""
            with self.llm_lock:
                reply = self.backend_router.send(prompt)

            self.emit("ai", "Trinity", reply)
            self.canvas_log("chat", "Trinity", reply)
            self.add_memory(reply, {"speaker": "trinity"})
        except Exception as e:
            self.emit("system", "System", f"Chat error: {e}")
        finally:
            self.thinking = False
            self.set_status("Ready.")

    def maybe_use_executive(self, task):
        if self.executive is None:
            return None
        try:
            return self.executive.route(task)
        except Exception as e:
            print("Executive route failed:", e)
            return None

    def run_shell_command(self, cmd):
        try:
            p = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=20)
            return (p.stdout + "\n" + p.stderr).strip()
        except Exception as e:
            return f"Shell command failed: {e}"

    def ollama_generate(self, prompt):
        payload = {
            "model": self.ollama_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "num_predict": self.max_tokens
            }
        }
        r = requests.post("http://127.0.0.1:11434/api/generate", json=payload, timeout=120)
        r.raise_for_status()
        data = r.json()
        return data.get("response", "").strip()

    def local_generate(self, prompt):
        if not self.local_model_loaded or self.llm is None:
            raise RuntimeError("Local model not loaded.")

        result = self.llm(
            prompt,
            max_tokens=min(self.max_tokens, 256),
            temperature=self.temperature,
            top_p=self.top_p,
            echo=False,
            stop=["</s>", "User:", "You:"]
        )

        if isinstance(result, dict):
            choices = result.get("choices", [])
            if choices:
                return choices[0].get("text", "").strip()

        return str(result).strip()

    def summarize_memory(self):
        if not self.memory:
            return "No memory stored."
        sample = "\n".join(m.get("text", "")[:500] for m in self.memory[-20:])
        prompt = f"Summarize these memory items into a compact profile:\n\n{sample}"
        return self.backend_router.send(prompt)

    def profile_user(self):
        try:
            profile = self.summarize_memory()
            self.canvas_log("profile", "System", profile)
            self.emit("system", "System", profile)
        except Exception as e:
            self.emit("system", "System", f"Profile generation failed: {e}")

    def self_reflect(self):
        try:
            recent = "\n".join([m.get("text", "")[:400] for m in self.memory[-15:]])
            prompt = f"""
Reflect on Trinity's recent interactions and identify:
- strengths
- repeated problems
- useful next improvements

Recent history:
{recent}
"""
            reflection = self.backend_router.send(prompt)
            self.canvas_log("reflection", "System", reflection)
            self.emit("system", "Reflection", reflection)
            self.add_memory(reflection, {"source": "self_reflection"})
        except Exception as e:
            self.emit("system", "System", f"Self reflection failed: {e}")

    def run_module(self, module_name, fn_name="main", *args, **kwargs):
        sys.path.insert(0, self.module_dir)
        try:
            mod = __import__(module_name)
            fn = getattr(mod, fn_name, None)
            if callable(fn):
                return fn(*args, **kwargs)
            return f"Function {fn_name} not found in module {module_name}"
        except Exception as e:
            return f"Module run failed: {e}"
        finally:
            if self.module_dir in sys.path:
                try:
                    sys.path.remove(self.module_dir)
                except Exception:
                    pass

    def bootstrap_module_template(self, module_name, goal):
        return f'''"""
Auto-generated Trinity module: {module_name}
Goal: {goal}
"""

def main(*args, **kwargs):
    return "Module {module_name} ready."
'''

    def ensure_module_exists(self, module_name, goal="General helper"):
        path = os.path.join(self.module_dir, f"{module_name}.py")
        if os.path.exists(path):
            return path
        with open(path, "w", encoding="utf-8") as f:
            f.write(self.bootstrap_module_template(module_name, goal))
        return path

    def inspect_module(self, module_name):
        path = os.path.join(self.module_dir, f"{module_name}.py")
        if not os.path.exists(path):
            return f"Module not found: {module_name}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                code = f.read()
            return code
        except Exception as e:
            return f"Inspect failed: {e}"

    def improve_module(self, module_name, instruction):
        path = os.path.join(self.module_dir, f"{module_name}.py")
        if not os.path.exists(path):
            return f"Module not found: {module_name}"
        try:
            with open(path, "r", encoding="utf-8") as f:
                current = f.read()
            prompt = f"""
You are improving a Trinity Python module.

MODULE NAME:
{module_name}

CURRENT CODE:
{current}

INSTRUCTION:
{instruction}

Return only the full revised Python code.
"""
            revised = self.backend_router.send(prompt)
            revised = self.extract_code_block(revised)
            with open(path, "w", encoding="utf-8") as f:
                f.write(revised)
            return f"Module improved: {module_name}"
        except Exception as e:
            return f"Improve module failed: {e}"

    def run_maintenance(self):
        try:
            self.profile_user()
            self.self_reflect()
            self.emit("system", "System", "Maintenance completed.")
        except Exception as e:
            self.emit("system", "System", f"Maintenance failed: {e}")

    def run_startup_checks(self):
        checks = []

        if self.backend_mode == "local":
            checks.append(f"Local model loaded: {self.local_model_loaded}")
        else:
            try:
                r = requests.get("http://127.0.0.1:11434/api/tags", timeout=5)
                checks.append(f"Ollama reachable: {r.status_code == 200}")
            except Exception:
                checks.append("Ollama reachable: False")

        checks.append(f"Vector memory ready: {self.vector_memory is not None}")
        checks.append(f"Executive ready: {self.executive is not None}")
        checks.append(f"Engine ready: {self.engine is not None}")

        for c in checks:
            self.emit("system", "Startup", c)

    def ingest_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            distilled = self.process_training_pass(text[:15000])
            self.add_memory(distilled, {"source": path})
            self.emit("system", "System", f"Ingested file: {path}")
        except Exception as e:
            self.emit("system", "System", f"File ingest failed: {e}")

    def ingest_folder(self, folder):
        try:
            files = []
            for root, _, names in os.walk(folder):
                for name in names:
                    if name.lower().endswith((".txt", ".md", ".py", ".json")):
                        files.append(os.path.join(root, name))
            for p in files[:50]:
                self.ingest_file(p)
            self.emit("system", "System", f"Ingested {len(files[:50])} files.")
        except Exception as e:
            self.emit("system", "System", f"Folder ingest failed: {e}")

    def route_special_commands(self, user_msg):
        msg = user_msg.strip()

        if msg == "/maintenance":
            threading.Thread(target=self.run_maintenance, daemon=True).start()
            return True

        if msg == "/profile":
            threading.Thread(target=self.profile_user, daemon=True).start()
            return True

        if msg.startswith("/runmodule "):
            parts = msg.split(maxsplit=1)
            if len(parts) == 2:
                module_name = parts[1].strip()
                out = self.run_module(module_name)
                self.emit("tool", "Module", str(out))
                return True

        if msg.startswith("/inspectmodule "):
            parts = msg.split(maxsplit=1)
            if len(parts) == 2:
                module_name = parts[1].strip()
                out = self.inspect_module(module_name)
                self.emit("tool", "Module", out)
                return True

        if msg.startswith("/improvemodule "):
            try:
                _, rest = msg.split(" ", 1)
                module_name, instruction = rest.split("::", 1)
                result = self.improve_module(module_name.strip(), instruction.strip())
                self.emit("system", "System", result)
                return True
            except Exception:
                self.emit("system", "System", "Usage: /improvemodule module_name :: instruction")
                return True

        if msg.startswith("/ingestfile "):
            p = msg.split(" ", 1)[1].strip()
            threading.Thread(target=self.ingest_file, args=(p,), daemon=True).start()
            return True

        if msg.startswith("/ingestfolder "):
            p = msg.split(" ", 1)[1].strip()
            threading.Thread(target=self.ingest_folder, args=(p,), daemon=True).start()
            return True

        return False


class BackendRouter:
    def __init__(self, app):
        self.app = app

    def send(self, prompt):
        if self.app.backend_mode == "local":
            if self.app.local_model_loaded and self.app.llm is not None:
                return self.app.local_generate(prompt)
            return "Local backend selected, but no model is loaded."
        return self.app.ollama_generate(prompt)


def install_dark_ttk(root):
    style = ttk.Style(root)
    try:
        style.theme_use("clam")
    except Exception:
        pass
    style.configure("TCombobox", fieldbackground="#111827", background="#111827", foreground="#00ffff")
    style.map("TCombobox",
              fieldbackground=[("readonly", "#111827")],
              foreground=[("readonly", "#00ffff")])


class TrinityHotkeys:
    def __init__(self, app):
        self.app = app
        self.bind()

    def bind(self):
        self.app.root.bind("<Control-Return>", lambda e: self.app.send_chat())
        self.app.root.bind("<Control-l>", lambda e: self.app.load_local_model())
        self.app.root.bind("<Control-r>", lambda e: self.app.reload_models())
        self.app.root.bind("<Escape>", lambda e: self.app.request_stop())


class TrinityDiagnostics:
    def __init__(self, app):
        self.app = app

    def run(self):
        out = []
        out.append(f"Python: {sys.version.split()[0]}")
        out.append(f"Platform: {platform.platform()}")
        out.append(f"Backend: {self.app.backend_mode}")
        out.append(f"LLAMA_AVAILABLE: {LLAMA_AVAILABLE}")
        out.append(f"Local loaded: {self.app.local_model_loaded}")
        out.append(f"Model selected: {self.app.model_var.get().strip()}")
        out.append(f"Memory items: {len(self.app.memory)}")
        out.append(f"Canvas items: {len(self.app.canvas.entries)}")
        return "\n".join(out)


class TrinityAgentPlanner:
    def __init__(self, app):
        self.app = app

    def create_plan(self, goal):
        prompt = f"""
Create a concise execution plan for the following goal.

GOAL:
{goal}

Return:
- objective
- steps
- risks
- success criteria
"""
        return self.app.backend_router.send(prompt)

    def critique_plan(self, plan):
        prompt = f"""
Critique the following plan and improve it.

PLAN:
{plan}
"""
        return self.app.backend_router.send(prompt)


class TrinityTaskRunner:
    def __init__(self, app):
        self.app = app
        self.planner = TrinityAgentPlanner(app)

    def run_task(self, task):
        self.app.emit("system", "System", f"TaskRunner received: {task}")
        plan = self.planner.create_plan(task)
        self.app.emit("agent", "Planner", plan)
        critique = self.planner.critique_plan(plan)
        self.app.emit("agent", "Critic", critique)
        final_prompt = f"""
Use the plan and critique below to complete the task.

TASK:
{task}

PLAN:
{plan}

CRITIQUE:
{critique}
"""
        result = self.app.backend_router.send(final_prompt)
        self.app.emit("ai", "Trinity", result)
        self.app.canvas_log("task_result", "TaskRunner", result)
        self.app.add_memory(result, {"source": "task_runner", "task": task})


class TrinityMemoryTrainer:
    def __init__(self, app):
        self.app = app

    def batch_train(self, texts):
        results = []
        for text in texts:
            if self.app.stop_requested:
                self.app.stop_requested = False
                break
            try:
                distilled = self.app.process_training_pass(text)
                self.app.add_memory(distilled, {"source": "batch_train"})
                results.append(distilled)
            except Exception as e:
                results.append(f"Training failed: {e}")
        return results


class TrinityCodeLab:
    def __init__(self, app):
        self.app = app

    def generate_script(self, request):
        prompt = f"""
Write a Python script for the following request:

{request}

Requirements:
- safe defaults
- include comments
- no markdown
"""
        return self.app.backend_router.send(prompt)

    def analyze_code(self, code):
        prompt = f"""
Review the following Python code and identify:
- bugs
- risks
- improvements

CODE:
{code}
"""
        return self.app.backend_router.send(prompt)


class TrinityWebResearch:
    def __init__(self, app):
        self.app = app

    def fetch(self, url):
        return self.app.open_browser_tool(url)

    def compare(self, urls):
        outputs = []
        for u in urls:
            outputs.append(f"URL: {u}\n{self.fetch(u)}")
        prompt = f"Compare the following research notes and produce a synthesis:\n\n" + "\n\n".join(outputs)
        return self.app.backend_router.send(prompt)


class TrinityPersona:
    def __init__(self, app):
        self.app = app
        self.mode = "balanced"

    def set_mode(self, mode):
        self.mode = mode

    def prefix(self):
        if self.mode == "balanced":
            return "Be helpful, accurate, and concise."
        if self.mode == "creative":
            return "Be imaginative, elegant, and engaging."
        if self.mode == "strict":
            return "Be precise, rigorous, and direct."
        return "Be helpful."

    def wrap(self, prompt):
        return f"{self.prefix()}\n\n{prompt}"


class TrinitySessionManager:
    def __init__(self, app):
        self.app = app
        self.file = os.path.join(app.base_dir, "memory", "session.json")

    def save(self):
        data = {
            "backend_mode": self.app.backend_mode,
            "ollama_model": self.app.ollama_model,
            "selected_model": self.app.model_var.get().strip(),
            "memory_count": len(self.app.memory),
            "canvas_count": len(self.app.canvas.entries),
            "time": datetime.now().isoformat()
        }
        safe_json_save(self.file, data)

    def load(self):
        return safe_json_load(self.file, {})


class TrinityPromptLibrary:
    def __init__(self):
        self.prompts = {
            "summarize": "Summarize the following content clearly and concisely.",
            "analyze": "Analyze the following content and identify the key insights.",
            "improve": "Improve the following text while preserving intent.",
            "extract": "Extract the most important facts from the following content."
        }

    def get(self, name):
        return self.prompts.get(name, "")

    def names(self):
        return sorted(self.prompts.keys())


class TrinityStats:
    def __init__(self, app):
        self.app = app

    def word_counts(self):
        texts = [m.get("text", "") for m in self.app.memory]
        counts = Counter()
        for t in texts:
            for w in re.findall(r"\b[a-zA-Z]{3,}\b", t.lower()):
                counts[w] += 1
        return counts.most_common(20)

    def memory_summary(self):
        return {
            "items": len(self.app.memory),
            "canvas": len(self.app.canvas.entries),
            "top_words": self.word_counts()
        }


class TrinityCommandBar:
    def __init__(self, app):
        self.app = app

    def handle(self, text):
        if self.app.route_special_commands(text):
            return True
        if text.startswith("/diag"):
            diag = TrinityDiagnostics(self.app).run()
            self.app.emit("system", "Diagnostics", diag)
            return True
        if text.startswith("/task "):
            task = text.split(" ", 1)[1].strip()
            threading.Thread(target=TrinityTaskRunner(self.app).run_task, args=(task,), daemon=True).start()
            return True
        return False


class TrinityShellTools:
    def __init__(self, app):
        self.app = app

    def list_dir(self, path="."):
        try:
            return "\n".join(sorted(os.listdir(path)))
        except Exception as e:
            return f"List dir failed: {e}"

    def read_file(self, path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return f.read()[:12000]
        except Exception as e:
            return f"Read file failed: {e}"

    def write_file(self, path, content):
        try:
            os.makedirs(os.path.dirname(path), exist_ok=True)
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            return f"Wrote file: {path}"
        except Exception as e:
            return f"Write file failed: {e}"


class TrinityKnowledgeDistiller:
    def __init__(self, app):
        self.app = app

    def distill_many(self, texts):
        joined = "\n\n".join(texts[:10])
        prompt = f"""
Distill the following knowledge into:
- key concepts
- principles
- compressed summary

CONTENT:
{joined}
"""
        return self.app.backend_router.send(prompt)


class TrinityConversationModes:
    def __init__(self, app):
        self.app = app
        self.mode = "normal"

    def set(self, mode):
        self.mode = mode

    def transform_prompt(self, prompt):
        if self.mode == "teacher":
            return "Explain clearly for learning.\n\n" + prompt
        if self.mode == "coder":
            return "Be engineering-focused and practical.\n\n" + prompt
        if self.mode == "research":
            return "Be analytical and evidence-seeking.\n\n" + prompt
        return prompt


class TrinityMemoryInspector:
    def __init__(self, app):
        self.app = app

    def recent(self, n=10):
        return self.app.memory[-n:]

    def find_by_keyword(self, kw):
        kw = kw.lower()
        return [m for m in self.app.memory if kw in m.get("text", "").lower()]

    def export_text(self):
        chunks = []
        for m in self.app.memory:
            chunks.append(m.get("text", ""))
        return "\n\n---\n\n".join(chunks)


class TrinityModuleFactory:
    def __init__(self, app):
        self.app = app

    def scaffold(self, module_name, description):
        code = f'''"""
Trinity module: {module_name}
Description: {description}
"""

def main(*args, **kwargs):
    return {repr(description)}
'''
        path = os.path.join(self.app.module_dir, f"{module_name}.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        return path

    def generate_with_llm(self, module_name, description):
        prompt = f"""
Create a Python module named {module_name}.

Description:
{description}

Return only Python code.
"""
        code = self.app.backend_router.send(prompt)
        code = self.app.extract_code_block(code)
        path = os.path.join(self.app.module_dir, f"{module_name}.py")
        with open(path, "w", encoding="utf-8") as f:
            f.write(code)
        return path


class TrinityAssistantCore:
    def __init__(self, app):
        self.app = app
        self.persona = TrinityPersona(app)
        self.modes = TrinityConversationModes(app)
        self.command_bar = TrinityCommandBar(app)

    def process(self, text):
        if self.command_bar.handle(text):
            return None

        prompt = self.app.build_context(text)
        prompt = self.persona.wrap(prompt)
        prompt = self.modes.transform_prompt(prompt)
        return self.app.backend_router.send(prompt)


def startup_banner(app):
    app.emit("system", "System", "MiniTrini v10.1 booting...")
    app.run_startup_checks()
    app.emit("system", "System", "Ready for conversation.")


def patch_entry_send_behavior(app):
    original = app.send_chat

    def wrapped():
        text = app.entry.get().strip()
        if not text:
            return
        if app.route_special_commands(text):
            app.entry.delete(0, "end")
            return
        original()

    app.send_chat = wrapped


def register_optional_tools(app):
    shell = TrinityShellTools(app)
    TOOLS["list_dir"] = {
        "desc": "List files in a directory.",
        "fn": lambda self, arg: shell.list_dir(arg or ".")
    }
    TOOLS["read_file"] = {
        "desc": "Read a text file.",
        "fn": lambda self, arg: shell.read_file(arg)
    }


def register_optional_commands(app):
    def send_override():
        text = app.entry.get().strip()
        if not text:
            return
        app.entry.delete(0, "end")
        app.emit("user", "You", text)
        app.add_memory(text, {"speaker": "user"})

        if app.route_special_commands(text):
            return

        if text.startswith("/agenttask "):
            task = text.split(" ", 1)[1].strip()
            threading.Thread(target=app.run_multi_agent, args=(task,), daemon=True).start()
            return

        threading.Thread(target=app._chat_worker, args=(text,), daemon=True).start()

    app.send_chat = send_override


def boot_extensions(app):
    register_optional_tools(app)
    register_optional_commands(app)
    TrinityHotkeys(app)
    TrinitySessionManager(app).save()


def _compat_engine_run(app, task):
    if app.engine is None:
        return "Engine not available."
    try:
        if hasattr(app.engine, "run"):
            return app.engine.run(task)
        if hasattr(app.engine, "execute"):
            return app.engine.execute(task)
        return "Engine has no run/execute method."
    except Exception as e:
        return f"Engine run failed: {e}"


def add_engine_tool(app):
    TOOLS["engine"] = {
        "desc": "Route a task through MiniTriniEngine.",
        "fn": lambda self, arg: _compat_engine_run(app, arg)
    }


def install_menu(app):
    menubar = tk.Menu(app.root, bg=BG, fg=FG)
    file_menu = tk.Menu(menubar, tearoff=0, bg=BG, fg=FG)
    file_menu.add_command(label="Save Settings", command=app.save_settings)
    file_menu.add_command(label="Export Canvas", command=app.export_canvas)
    file_menu.add_separator()
    file_menu.add_command(label="Exit", command=app.root.destroy)
    menubar.add_cascade(label="File", menu=file_menu)

    tools_menu = tk.Menu(menubar, tearoff=0, bg=BG, fg=FG)
    tools_menu.add_command(label="Diagnostics", command=lambda: app.emit("system", "Diagnostics", TrinityDiagnostics(app).run()))
    tools_menu.add_command(label="Profile User", command=app.profile_user)
    tools_menu.add_command(label="Self Reflect", command=app.self_reflect)
    tools_menu.add_command(label="Maintenance", command=app.run_maintenance)
    menubar.add_cascade(label="Tools", menu=tools_menu)

    app.root.config(menu=menubar)


def wire_secondary_features(app):
    app.persona = TrinityPersona(app)
    app.prompt_library = TrinityPromptLibrary()
    app.stats = TrinityStats(app)
    app.session = TrinitySessionManager(app)
    app.code_lab = TrinityCodeLab(app)
    app.memory_trainer = TrinityMemoryTrainer(app)
    app.web_research = TrinityWebResearch(app)
    app.module_factory = TrinityModuleFactory(app)
    app.assistant_core = TrinityAssistantCore(app)
    add_engine_tool(app)


def extend_special_commands(app):
    original_route = app.route_special_commands

    def extended(msg):
        if original_route(msg):
            return True

        if msg.startswith("/mode "):
            mode = msg.split(" ", 1)[1].strip()
            app.assistant_core.modes.set(mode)
            app.emit("system", "System", f"Conversation mode set to: {mode}")
            return True

        if msg.startswith("/persona "):
            mode = msg.split(" ", 1)[1].strip()
            app.assistant_core.persona.set_mode(mode)
            app.emit("system", "System", f"Persona mode set to: {mode}")
            return True

        if msg.startswith("/summarizememory"):
            summary = app.summarize_memory()
            app.emit("system", "MemorySummary", summary)
            return True

        if msg.startswith("/stats"):
            stats = app.stats.memory_summary()
            app.emit("system", "Stats", json.dumps(stats, indent=2))
            return True

        if msg.startswith("/genscript "):
            request = msg.split(" ", 1)[1].strip()
            out = app.code_lab.generate_script(request)
            app.emit("ai", "CodeLab", out)
            return True

        if msg.startswith("/analyzecode "):
            path = msg.split(" ", 1)[1].strip()
            shell = TrinityShellTools(app)
            code = shell.read_file(path)
            out = app.code_lab.analyze_code(code)
            app.emit("ai", "CodeLab", out)
            return True

        if msg.startswith("/compareurls "):
            urls = [u for u in msg.split(" ")[1:] if u.strip()]
            out = app.web_research.compare(urls)
            app.emit("ai", "Research", out)
            return True

        if msg.startswith("/scaffoldmodule "):
            payload = msg.split(" ", 1)[1].strip()
            if "::" in payload:
                module_name, desc = payload.split("::", 1)
                path = app.module_factory.scaffold(module_name.strip(), desc.strip())
                app.emit("system", "System", f"Scaffolded module: {path}")
            else:
                app.emit("system", "System", "Usage: /scaffoldmodule name :: description")
            return True

        if msg.startswith("/gencode "):
            payload = msg.split(" ", 1)[1].strip()
            if "::" in payload:
                module_name, desc = payload.split("::", 1)
                path = app.module_factory.generate_with_llm(module_name.strip(), desc.strip())
                app.emit("system", "System", f"Generated module: {path}")
            else:
                app.emit("system", "System", "Usage: /gencode name :: description")
            return True

        if msg.startswith("/inspectmemory "):
            kw = msg.split(" ", 1)[1].strip()
            inspector = TrinityMemoryInspector(app)
            results = inspector.find_by_keyword(kw)
            preview = "\n\n".join([r.get("text", "")[:1000] for r in results[:5]]) or "No hits."
            app.emit("system", "MemoryInspector", preview)
            return True

        return False

    app.route_special_commands = extended


def enhance_chat_worker(app):
    original_worker = app._chat_worker

    def new_worker(user_msg):
        if app.stop_requested:
            app.stop_requested = False
            app.emit("system", "System", "Stop was already requested.")
        try:
            if app.executive is not None:
                routed = app.maybe_use_executive(user_msg)
                if routed and isinstance(routed, str):
                    app.canvas_log("executive", "Executive", routed)
            return original_worker(user_msg)
        except Exception as e:
            app.emit("system", "System", f"Enhanced chat worker failed: {e}")

    app._chat_worker = new_worker


def add_quick_buttons(app):
    quick = tk.Frame(app.root, bg=BG)
    quick.pack(fill="x", padx=10, pady=(0, 8))

    tk.Button(quick, text="Profile", command=app.profile_user, bg=ACCENT, fg="black").pack(side="left", padx=3)
    tk.Button(quick, text="Reflect", command=app.self_reflect, bg=FG, fg="black").pack(side="left", padx=3)
    tk.Button(quick, text="Diagnostics", command=lambda: app.emit("system", "Diagnostics", TrinityDiagnostics(app).run()), bg=ACCENT, fg="black").pack(side="left", padx=3)
    tk.Button(quick, text="Summarize Memory", command=lambda: app.emit("system", "Memory", app.summarize_memory()), bg=FG, fg="black").pack(side="left", padx=3)


def add_footer_note(app):
    note = tk.Label(
        app.root,
        text="Commands: /diag /task ... /profile /maintenance /genscript ... /gencode name :: description",
        fg="#7dd3fc",
        bg=BG,
        anchor="w",
        font=("JetBrains Mono", 9)
    )
    note.pack(fill="x", padx=10, pady=(0, 6))


def normalize_memory(app):
    fixed = []
    for m in app.memory:
        if isinstance(m, str):
            fixed.append({"time": datetime.now().isoformat(), "text": m, "meta": {}})
        elif isinstance(m, dict):
            fixed.append({
                "time": m.get("time", datetime.now().isoformat()),
                "text": m.get("text", ""),
                "meta": m.get("meta", {})
            })
    app.memory = fixed
    safe_json_save(app.memory_path, app.memory)
    app.refresh_memory_list()


def ensure_prompt_seed(app):
    seed_path = os.path.join(app.base_dir, "memory", "system_seed.txt")
    if not os.path.exists(seed_path):
        with open(seed_path, "w", encoding="utf-8") as f:
            f.write("Trinity should be helpful, reflective, and practical.")
    try:
        with open(seed_path, "r", encoding="utf-8") as f:
            seed = f.read().strip()
        app.add_memory(f"[SYSTEM_SEED] {seed}", {"seed": True})
    except Exception:
        pass


def add_research_tool(app):
    TOOLS["compare_urls"] = {
        "desc": "Compare and synthesize multiple URLs separated by spaces.",
        "fn": lambda self, arg: TrinityWebResearch(app).compare(arg.split())
    }


def add_memory_tools(app):
    inspector = TrinityMemoryInspector(app)
    TOOLS["memory_recent"] = {
        "desc": "Return recent memory items.",
        "fn": lambda self, arg: json.dumps(inspector.recent(int(arg) if str(arg).isdigit() else 5), indent=2)
    }
    TOOLS["memory_export"] = {
        "desc": "Export memory as text.",
        "fn": lambda self, arg: inspector.export_text()[:12000]
    }


def add_shell_tools(app):
    shell = TrinityShellTools(app)
    TOOLS["shell"] = {
        "desc": "Run a shell command.",
        "fn": lambda self, arg: app.run_shell_command(arg)
    }
    TOOLS["write_file"] = {
        "desc": "Write content to a file using PATH::CONTENT format.",
        "fn": lambda self, arg: shell.write_file(*arg.split("::", 1)) if "::" in arg else "Use PATH::CONTENT"
    }


def backfill_vector_memory(app):
    if app.vector_memory is None:
        return
    try:
        for item in app.memory[-50:]:
            text = item.get("text", "")
            if text:
                app.vector_memory.add_memory(text, metadata=item.get("meta", {}))
    except Exception as e:
        print("Backfill vector memory failed:", e)


def extend_decide_tools(app):
    original = app.decide_tools

    def wrapped(user_msg):
        calls = original(user_msg)
        msg = user_msg.lower()
        if msg.startswith("compare urls "):
            payload = user_msg[len("compare urls "):].strip()
            if payload:
                calls.append(("compare_urls", payload))
        if msg.startswith("recent memory"):
            calls.append(("memory_recent", "5"))
        return calls

    app.decide_tools = wrapped


def add_training_ui(app):
    pass


def attach_context_enricher(app):
    original = app.build_context

    def wrapped(latest_user_msg):
        base = original(latest_user_msg)
        summary = ""
        try:
            summary = app.summarize_memory()
        except Exception:
            summary = ""
        return f"{base}\n\nCompact Profile:\n{summary}\n"

    app.build_context = wrapped


def add_startup_memory(app):
    app.add_memory("MiniTrini started successfully.", {"startup": True})


def attach_module_runner_to_tools(app):
    TOOLS["run_module"] = {
        "desc": "Run a module by name.",
        "fn": lambda self, arg: app.run_module(arg.strip())
    }


def install_background_jobs(app):
    def periodic_save():
        try:
            if hasattr(app, "session"):
                app.session.save()
        except Exception:
            pass
        app.root.after(30000, periodic_save)

    app.root.after(30000, periodic_save)


def add_help_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/help":
            help_text = """
Available commands:
/help
/diag
/profile
/maintenance
/task <task>
/agenttask <task>
/runmodule <name>
/inspectmodule <name>
/improvemodule <name> :: <instruction>
/ingestfile <path>
/ingestfolder <path>
/mode <teacher|coder|research|normal>
/persona <balanced|creative|strict>
/summarizememory
/stats
/genscript <request>
/analyzecode <path>
/compareurls <url1> <url2> ...
/scaffoldmodule <name> :: <description>
/gencode <name> :: <description>
/inspectmemory <keyword>
"""
            app.emit("system", "Help", help_text)
            return True
        return False

    app.route_special_commands = wrapped


def attach_safe_send_guard(app):
    orig_send = app.backend_router.send

    def wrapped(prompt):
        if not isinstance(prompt, str):
            prompt = str(prompt)
        if not prompt.strip():
            return "Empty prompt."
        return orig_send(prompt)

    app.backend_router.send = wrapped


def install_app_identity(app):
    app.identity = {
        "name": "Trinity",
        "version": "10.1",
        "edition": "Multi-Agent",
        "backend": lambda: app.backend_mode
    }


def add_thought_scaffold(app):
    def scaffold(question):
        return f"""
Think through the problem carefully.

QUESTION:
{question}

Return:
- understanding
- approach
- answer
"""
    app.thought_scaffold = scaffold


def add_reflection_tool(app):
    TOOLS["reflect"] = {
        "desc": "Perform self reflection on recent memory.",
        "fn": lambda self, arg: app.self_reflect() or "Reflection completed."
    }


def add_summary_tool(app):
    TOOLS["summarize_memory"] = {
        "desc": "Summarize memory.",
        "fn": lambda self, arg: app.summarize_memory()
    }


def install_memory_buttons(app):
    extra = tk.Frame(app.root, bg=BG)
    extra.pack(fill="x", padx=10, pady=(0, 6))
    tk.Button(extra, text="Memory Search", command=app.memory_search_prompt, bg=ACCENT, fg="black").pack(side="left", padx=3)
    tk.Button(extra, text="Train Memory", command=app.train_memory_prompt, bg=FG, fg="black").pack(side="left", padx=3)
    tk.Button(extra, text="Run Agents", command=app.run_agents_prompt, bg=ACCENT, fg="black").pack(side="left", padx=3)
    tk.Button(extra, text="Help", command=lambda: app.emit("system", "Help", "Type /help for commands."), bg=FG, fg="black").pack(side="left", padx=3)


def patch_send_chat_with_assistant_core(app):
    def send_chat():
        text = app.entry.get().strip()
        if not text:
            return
        app.entry.delete(0, "end")
        app.emit("user", "You", text)
        app.add_memory(text, {"speaker": "user"})

        if app.route_special_commands(text):
            return

        def worker():
            app.set_status("Thinking...")
            try:
                tool_results = []
                if app.auto_tool_mode:
                    for tool_name, arg in app.decide_tools(text):
                        try:
                            result = TOOLS[tool_name]["fn"](app, arg)
                            tool_results.append((tool_name, arg, result))
                            app.emit("tool", tool_name, str(result))
                        except Exception as e:
                            tool_results.append((tool_name, arg, f"Tool error: {e}"))

                base_prompt = app.build_context(text)
                tool_context = "\n".join([f"{n}({a}) => {r}" for n, a, r in tool_results])
                final_prompt = f"{base_prompt}\n\nTool Results:\n{tool_context}\n"
                final_prompt = app.assistant_core.persona.wrap(final_prompt)
                final_prompt = app.assistant_core.modes.transform_prompt(final_prompt)
                reply = app.backend_router.send(final_prompt)
                app.emit("ai", "Trinity", reply)
                app.canvas_log("chat", "Trinity", reply)
                app.add_memory(reply, {"speaker": "trinity"})
            except Exception as e:
                app.emit("system", "System", f"Chat failed: {e}")
            finally:
                app.set_status("Ready.")

        threading.Thread(target=worker, daemon=True).start()

    app.send_chat = send_chat


def install_model_auto_select(app):
    models = app.get_model_list()
    app.model_menu["values"] = models
    if models:
        app.model_var.set(models[0])
        if app.backend_mode == "local":
            try:
                app.load_local_model()
            except Exception as e:
                app.emit("system", "System", f"Auto-load failed: {e}")


def register_system_memory(app):
    app.add_memory(
        "Trinity is a local-first multi-agent assistant with memory, tools, and module generation.",
        {"system": True}
    )


def install_module_examples(app):
    examples_dir = os.path.join(app.base_dir, "modules")
    os.makedirs(examples_dir, exist_ok=True)

    hello_path = os.path.join(examples_dir, "hello_trinity.py")
    if not os.path.exists(hello_path):
        with open(hello_path, "w", encoding="utf-8") as f:
            f.write(
                'def main(*args, **kwargs):\n'
                '    return "Hello from Trinity module."\n'
            )


def install_quality_checks(app):
    def quality_check(text):
        if not text or not text.strip():
            return False, "Empty text."
        if len(text.strip()) < 2:
            return False, "Text too short."
        return True, "OK"

    app.quality_check = quality_check


def attach_safe_memory_add(app):
    orig = app.add_memory

    def wrapped(text, meta=None):
        ok, _ = app.quality_check(text)
        if not ok:
            return
        return orig(text, meta)

    app.add_memory = wrapped


def add_prompt_templates(app):
    app.templates = {
        "deep_analysis": """
Analyze the following deeply:
- assumptions
- risks
- opportunities
- recommendation

CONTENT:
{content}
""",
        "rewrite": """
Rewrite the following text for clarity and quality.

TEXT:
{content}
""",
        "extract_actions": """
Extract concrete action items from the following content.

CONTENT:
{content}
"""
    }


def use_template(app, template_name, content):
    tpl = app.templates.get(template_name, "{content}")
    return tpl.format(content=content)


def add_template_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/template "):
            try:
                payload = msg.split(" ", 1)[1]
                name, content = payload.split("::", 1)
                prompt = use_template(app, name.strip(), content.strip())
                out = app.backend_router.send(prompt)
                app.emit("ai", "Template", out)
            except Exception:
                app.emit("system", "System", "Usage: /template template_name :: content")
            return True
        return False

    app.route_special_commands = wrapped


def install_file_drop_stub(app):
    app.file_drop_enabled = False


def add_orb_status_sync(app):
    orig_set_status = app.set_status

    def wrapped(text):
        orig_set_status(text)
        try:
            app.orb.itemconfig(app.orb.text, text="TRINITY")
        except Exception:
            pass

    app.set_status = wrapped


def add_memory_snapshot_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/snapshot":
            path = os.path.join(app.base_dir, "memory", f"snapshot_{int(time.time())}.json")
            safe_json_save(path, app.memory)
            app.emit("system", "System", f"Memory snapshot saved: {path}")
            return True
        return False

    app.route_special_commands = wrapped


def add_canvas_snapshot_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/canvasdump":
            payload = json.dumps(app.canvas.export(), indent=2)
            app.emit("system", "Canvas", payload[:12000])
            return True
        return False

    app.route_special_commands = wrapped


def install_builtin_knowledge(app):
    app.builtin_knowledge = {
        "purpose": "Assist with reasoning, research, writing, coding, and memory-based workflows.",
        "limits": "Knowledge quality depends on backend, context, and available tools."
    }


def add_builtin_knowledge_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/about":
            app.emit("system", "About", json.dumps(app.builtin_knowledge, indent=2))
            return True
        return False

    app.route_special_commands = wrapped


def install_context_limits(app):
    app.context_char_limit = 12000


def patch_build_context_limit(app):
    orig = app.build_context

    def wrapped(latest_user_msg):
        text = orig(latest_user_msg)
        if len(text) > app.context_char_limit:
            return text[-app.context_char_limit:]
        return text

    app.build_context = wrapped


def add_memory_repair(app):
    repaired = False
    for m in app.memory:
        if "text" not in m:
            m["text"] = ""
            repaired = True
        if "meta" not in m:
            m["meta"] = {}
            repaired = True
        if "time" not in m:
            m["time"] = datetime.now().isoformat()
            repaired = True
    if repaired:
        safe_json_save(app.memory_path, app.memory)


def add_model_hint(app):
    if app.backend_mode == "local" and not app.local_model_loaded:
        app.emit("system", "System", "Hint: select a local model or switch backend.")


def install_ollama_model_sync(app):
    app.settings["ollama_model"] = app.ollama_model


def attach_prompt_debugger(app):
    app.debug_prompts = False

    orig_send = app.backend_router.send

    def wrapped(prompt):
        if getattr(app, "debug_prompts", False):
            app.emit("system", "PromptDebug", prompt[:8000])
        return orig_send(prompt)

    app.backend_router.send = wrapped


def add_debug_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/debugprompts on":
            app.debug_prompts = True
            app.emit("system", "System", "Prompt debugging enabled.")
            return True
        if msg.strip() == "/debugprompts off":
            app.debug_prompts = False
            app.emit("system", "System", "Prompt debugging disabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_autosave_memory(app):
    orig_add = app.add_memory

    def wrapped(text, meta=None):
        result = orig_add(text, meta)
        try:
            safe_json_save(app.memory_path, app.memory)
        except Exception:
            pass
        return result

    app.add_memory = wrapped


def install_chat_clear_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/clearchat":
            app.chat.delete("1.0", "end")
            app.emit("system", "System", "Chat cleared.")
            return True
        return False

    app.route_special_commands = wrapped


def install_memory_delete_last(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/popmemory":
            if app.memory:
                app.memory.pop()
                safe_json_save(app.memory_path, app.memory)
                app.refresh_memory_list()
                app.emit("system", "System", "Last memory item removed.")
            else:
                app.emit("system", "System", "No memory to remove.")
            return True
        return False

    app.route_special_commands = wrapped


def install_canvas_add_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/canvas "):
            text = msg.split(" ", 1)[1].strip()
            app.canvas_log("manual", "User", text)
            app.emit("system", "System", "Added to canvas.")
            return True
        return False

    app.route_special_commands = wrapped


def install_module_list_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/listmodules":
            files = [f for f in os.listdir(app.module_dir) if f.endswith(".py")]
            app.emit("system", "Modules", "\n".join(sorted(files)) or "No modules.")
            return True
        return False

    app.route_special_commands = wrapped


def install_memory_list_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/listmemory":
            preview = "\n".join([m.get("text", "")[:120] for m in app.memory[-20:]]) or "No memory."
            app.emit("system", "Memory", preview)
            return True
        return False

    app.route_special_commands = wrapped


def install_backend_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/backend":
            app.emit("system", "Backend", app.backend_mode)
            return True
        return False

    app.route_special_commands = wrapped


def install_set_ollama_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/setollama "):
            model_name = msg.split(" ", 1)[1].strip()
            app.ollama_model = model_name
            app.settings["ollama_model"] = model_name
            safe_json_save(app.config_path, app.settings)
            app.emit("system", "System", f"Ollama model set to: {model_name}")
            return True
        return False

    app.route_special_commands = wrapped


def install_train_batch_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/trainbatch "):
            path = msg.split(" ", 1)[1].strip()
            try:
                with open(path, "r", encoding="utf-8") as f:
                    chunks = [c.strip() for c in f.read().split("\n\n") if c.strip()]
                results = app.memory_trainer.batch_train(chunks[:20])
                app.emit("system", "BatchTrain", "\n\n".join(results[:10]))
            except Exception as e:
                app.emit("system", "System", f"Batch train failed: {e}")
            return True
        return False

    app.route_special_commands = wrapped


def install_browser_quick_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/browse "):
            url = msg.split(" ", 1)[1].strip()
            out = app.open_browser_tool(url)
            app.emit("tool", "Browser", out)
            return True
        return False

    app.route_special_commands = wrapped


def install_wiki_quick_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/wiki "):
            query = msg.split(" ", 1)[1].strip()
            out = app.wikipedia_tool(query)
            app.emit("tool", "Wiki", out)
            return True
        return False

    app.route_special_commands = wrapped


def install_calc_quick_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/calc "):
            expr = msg.split(" ", 1)[1].strip()
            out = app.calculator_tool(expr)
            app.emit("tool", "Calc", out)
            return True
        return False

    app.route_special_commands = wrapped


def install_research_mode_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/researchmode":
            app.assistant_core.modes.set("research")
            app.emit("system", "System", "Research mode enabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_teacher_mode_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/teachermode":
            app.assistant_core.modes.set("teacher")
            app.emit("system", "System", "Teacher mode enabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_coder_mode_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/codermode":
            app.assistant_core.modes.set("coder")
            app.emit("system", "System", "Coder mode enabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_balanced_persona_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/balanced":
            app.assistant_core.persona.set_mode("balanced")
            app.emit("system", "System", "Balanced persona enabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_creative_persona_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/creative":
            app.assistant_core.persona.set_mode("creative")
            app.emit("system", "System", "Creative persona enabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_strict_persona_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/strict":
            app.assistant_core.persona.set_mode("strict")
            app.emit("system", "System", "Strict persona enabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_tool_toggle_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/tools on":
            app.auto_tool_mode = True
            app.emit("system", "System", "Auto-tool mode enabled.")
            return True
        if msg.strip() == "/tools off":
            app.auto_tool_mode = False
            app.emit("system", "System", "Auto-tool mode disabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_voice_toggle_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.strip() == "/voice on":
            app.voice_enabled = True
            app.emit("system", "System", "Voice enabled.")
            return True
        if msg.strip() == "/voice off":
            app.voice_enabled = False
            app.emit("system", "System", "Voice disabled.")
            return True
        return False

    app.route_special_commands = wrapped


def install_prompt_scaffold_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/scaffold "):
            question = msg.split(" ", 1)[1].strip()
            scaffold = app.thought_scaffold(question)
            app.emit("system", "Scaffold", scaffold)
            return True
        return False

    app.route_special_commands = wrapped


def install_direct_prompt_command(app):
    old_route = app.route_special_commands

    def wrapped(msg):
        if old_route(msg):
            return True
        if msg.startswith("/prompt "):
            prompt = msg.split(" ", 1)[1].strip()
            out = app.backend_router.send(prompt)
            app.emit("ai", "DirectPrompt", out)
            return True
        return False

    app.route_special_commands = wrapped


def install_status_bar_enhancer(app):
    old_set = app.set_status

    def wrapped(text):
        old_set(f"[{datetime.now().strftime('%H:%M:%S')}] {text}")

    app.set_status = wrapped


def install_app(app):
    install_dark_ttk(app.root)
    startup_banner(app)
    boot_extensions(app)
    wire_secondary_features(app)
    extend_special_commands(app)
    enhance_chat_worker(app)
    add_quick_buttons(app)
    add_footer_note(app)
    normalize_memory(app)
    ensure_prompt_seed(app)
    add_research_tool(app)
    add_memory_tools(app)
    add_shell_tools(app)
    backfill_vector_memory(app)
    extend_decide_tools(app)
    attach_context_enricher(app)
    add_startup_memory(app)
    attach_module_runner_to_tools(app)
    install_background_jobs(app)
    add_help_command(app)
    attach_safe_send_guard(app)
    install_app_identity(app)
    add_thought_scaffold(app)
    add_reflection_tool(app)
    add_summary_tool(app)
    install_memory_buttons(app)
    patch_send_chat_with_assistant_core(app)
    install_model_auto_select(app)
    register_system_memory(app)
    install_module_examples(app)
    install_quality_checks(app)
    attach_safe_memory_add(app)
    add_prompt_templates(app)
    add_template_command(app)
    install_file_drop_stub(app)
    add_orb_status_sync(app)
    add_memory_snapshot_command(app)
    add_canvas_snapshot_command(app)
    install_builtin_knowledge(app)
    add_builtin_knowledge_command(app)
    install_context_limits(app)
    patch_build_context_limit(app)
    add_memory_repair(app)
    add_model_hint(app)
    install_ollama_model_sync(app)
    attach_prompt_debugger(app)
    add_debug_command(app)
    install_autosave_memory(app)
    install_chat_clear_command(app)
    install_memory_delete_last(app)
    install_canvas_add_command(app)
    install_module_list_command(app)
    install_memory_list_command(app)
    install_backend_command(app)
    install_set_ollama_command(app)
    install_train_batch_command(app)
    install_browser_quick_command(app)
    install_wiki_quick_command(app)
    install_calc_quick_command(app)
    install_research_mode_command(app)
    install_teacher_mode_command(app)
    install_coder_mode_command(app)
    install_balanced_persona_command(app)
    install_creative_persona_command(app)
    install_strict_persona_command(app)
    install_tool_toggle_command(app)
    install_voice_toggle_command(app)
    install_prompt_scaffold_command(app)
    install_direct_prompt_command(app)
    install_status_bar_enhancer(app)
    install_menu(app)


if __name__ == "__main__":
    root = tk.Tk()
    app = MiniTriniV10(root)
    install_app(app)

    app.model_menu.bind("<<ComboboxSelected>>", app.load_local_model)

    if app.backend_mode == "local":
        models = list(app.model_menu["values"])
        if models:
            app.model_var.set(models[0])
            app.load_local_model()

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