#!/usr/bin/env python3
# MiniTrini_v10 — Trinity Multi-Agent Edition with Pulse Glow + Training Engine

import time
import tkinter as tk
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
from TrinityCanvas import open_canvas, send_to_canvas
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


# -----------------------------
#  AGENTS (PRIMARY VERSION)
# -----------------------------
AGENTS = [
    {"icon":"👑", "name":"Trini", "overlay":"Core sovereign intelligence.", "tone":"balanced"},
    {"icon":"🧑‍💻", "name":"Developer", "overlay":"Think like a senior engineer.", "tone":"analytical"},
    {"icon":"🛡️", "name":"Security",  "overlay":"Evaluate threats, harden logic.", "tone":"formal"},
    {"icon":"🧠", "name":"Reasoning", "overlay":"Break problems into steps.", "tone":"neutral"},
    {"icon":"🔍", "name":"Research",  "overlay":"Search mentally, analyze context.", "tone":"curious"},
    {"icon":"🔧", "name":"Optimizer", "overlay":"Improve efficiency and quality.", "tone":"precise"},
    {"icon":"🧹", "name":"Refactor",  "overlay":"Clean messy structure calmly.", "tone":"calm"},
    {"icon":"⌛", "name":"Memory",    "overlay":"Recall and restructure history.", "tone":"gentle"},
    {"icon":"⚙️", "name":"System",    "overlay":"Execute command-style tasks safely.", "tone":"neutral"},
]

# -----------------------------
#  TOOLS
# -----------------------------
TOOLS = [
    {"icon":"🔧", "name":"Optimize",       "intent":"optimize",        "tone":"precise"},
    {"icon":"🧹", "name":"Refactor",       "intent":"refactor",        "tone":"calm"},
    {"icon":"💬", "name":"Explain",        "intent":"explain",         "tone":"gentle"},
    {"icon":"📝", "name":"Summarize",      "intent":"summarize",       "tone":"structured"},
    {"icon":"📐", "name":"Improve Prompt", "intent":"prompt_improve",  "tone":"neutral"},
    {"icon":"🔍", "name":"Analyze",        "intent":"analyze",         "tone":"analytical"},
    {"icon":"💡", "name":"Expand",         "intent":"expand",          "tone":"creative"},
    {"icon":"✂️", "name":"Reduce",         "intent":"reduce",          "tone":"minimal"},
]


# ======================================================================
#  MINI TRINI APP — CLEAN, STRUCTURALLY RESTORED
# ======================================================================
class MiniTriniApp:
    def __init__(self, root):
        self.root = root
        root.title("🧠 MiniTrini v10 — Multi-Agent Trinity Console")
        root.configure(bg=BG_MAIN)
        root.geometry("1080x800")
        #self.vector_memory = TriniVectorMemory(Path(__file__).resolve().parent)   
        PROJECT_ROOT = Path(__file__).resolve().parent
        MEMORY_DIR = PROJECT_ROOT / "AI_Core" / "TrinityMemoryBank" / "trained_memory"

        self.vector_memory = TriniVectorMemory(MEMORY_DIR)        
                     

        # Backend state
        self.backend_mode = "local"
        self.llm = None
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

        self.init_state_engine()
        self.state["memory_items"] = 0
        self.state["tokens"] = 0
        self.state["pipeline"] = []

        self.state_set_agent(self.active_agent["name"])

        self.backend_process = None
        self.core_runtime_window = None

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
        # Attach menu to the window
        menubar.add_cascade(label="Developer", menu=dev_menu)
        self.root.config(menu=menubar)

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
        if self.devtools_window and self.devtools_active:
            self.close_devtools()
        else:
            self.open_devtools()


        
        

    def state_set_task(self, task):
        self.state["task"] = task
        self.state["status"] = "Running"
        self.update_devtools()


    def display_message(self, sender, message):
        """
        Unified output renderer for MiniTrini v10.
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
                "max_tokens": 96,
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
            self.console_box.insert("end", message + "\n")
            self.console_box.see("end")   
            
            self.console_log(f"[Backend Error] {e}")
            self.console_log(f"[Local LLM Error] {e}")
            self.console_log(f"[Tool Error] {e}")
            self.console_log(f"[Training Error] {e}")
            self.console_log(f"[MiniTrini Error] {e}")
                         
    # ==================================================================
    #  UI BUILD
    # ==================================================================
    def build_ui(self):
        header = tk.Frame(self.root, bg=BG_MAIN)
        header.pack(fill="x", pady=8)

        tk.Label(
            header,
            text="🧠 MiniTrini v10 — ",
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
            

    def process_user_input(self, text):
        self.memory.append(("User", text))
        self.state_set_task("Processing user input")
        self.start_thinking_animation()

        # TOOL TRANSFORM
        tool_name = self.state.get("tool")
        if tool_name:
            tool = next((t for t in TOOLS if t["name"] == tool_name), None)
            if tool:
                text = self.run_tool_logic(tool, text)

        # BACKEND PROMPT
        agent_name = self.state.get("agent")
        tool_name  = self.state.get("tool")
        tool_obj = next((x for x in TOOLS if x["name"] == tool_name), None) if tool_name else None

        backend_prompt = self.build_backend_prompt(agent_name, tool_obj, text)

        # BACKEND CALL
        try:
            response_text = self.send_to_backend(backend_prompt)
        except Exception as e:
            response_text = f"[ERROR] Backend failed: {e}"
            self.state["last_error"] = str(e)
            self.pipeline(f"Backend responded ({self.backend_mode})") 
            
        self.clear_thinking()
        self.display_message("Assistant", response_text)
        self.memory.append(("Assistant", response_text))        

        if self.state.get("agent") == "Trini" and not response_text.startswith("[ERROR]"):
            self.vector_memory.add_memory(response_text)
            print("ADD MEMORY START")
            
        self.state["task"] = f"Running {agent_name}/{tool_name}"
        self.state["status"] = "Running"
        self.update_devtools()

    def toggle_sara_mode(self):
        self.sara_mode = not self.sara_mode

        if self.sara_mode:
            self.pipeline("SARA Mode → USER-ACTIVATED")
        else:
            self.pipeline("SARA Mode → OFF")

        self.update_devtools()

    def activate_sara_autopilot(self, reason):
        self.sara_autopilot = True
        self.pipeline(f"SARA Autopilot → {reason}")
        self.update_devtools()
        
        # --- AUTO SARA ACTIVATION RULES ---

        # 1. Drift detected previously
        if self.state.get("last_error") or self.detect_drift(text):
            self.activate_sara_autopilot("Drift detected")

        # 2. Complex queries (heuristic)
        if len(text.split()) > 25 or "why" in text.lower() or "how" in text.lower():
            self.activate_sara_autopilot("High complexity reasoning")

        # 3. Tool-based activation (Analyze, Optimize, Refactor)
        if self.state.get("tool") in ["Analyze", "Optimize", "Refactor"]:
            self.activate_sara_autopilot("Tool requires structured reasoning")        
    # ==================================================================
    #  BACKEND PROMPT BUILDER
    # ==================================================================
    def build_backend_prompt(self, agent, tool, user_text):

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
            f"[Agent: {agent}]\n" +
            (f"[Tool: {tool['name']}]\n" if tool else "[Tool: None]\n") +
            TRINITY_TONE
        )

        return self.apply_sara_framework(
            header + "\n" + user_text.strip()
        )
    def load_trini_memory_context(self):
        memory_dir = Path(__file__).resolve().parent / "AI_Core" / "TrinityMemoryBank" / "trained_memory"

        files = sorted(memory_dir.glob("*.txt"), reverse=True)[:5]

        context = ""
        for f in files:
            context += f.read_text() + "\n"

        return f"[Trini Memory Context]\n{context}"

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
    #  BACKEND ROUTING
    # ==================================================================    

    def send_to_backend(self, prompt_text):
        
        # --- Normalize the model-ready prompt (strip headers) ---
        final_prompt = self.clean_for_model(prompt_text)

        # --- LOCAL BACKEND (llama.cpp) ---
        if self.backend_mode == "local":
            if not self.llm:
                return "[ERROR] No local model loaded."

            try:
                result = self.llm(
                    prompt = final_prompt,
                    max_tokens = 256 if self.speed_profile == "runtime" else 96,
                    temperature = 0.7,
                    stop = ["User:", "Assistant:"]
                )

                llm_text = self.extract_llama_output(result)

                code = self.extract_code_block(llm_text)
                if code:
                    send_to_canvas(code, "generated.py")

                return llm_text

            except Exception as e:
                return f"[ERROR] Local LLM failure: {e}"
                
    def extract_code_block(self, text):
        if "```" not in text:
            return None
        try:
            section = text.split("```", 1)[1]
            # skip language tag if present
            if "\n" in section:
                section = section.split("\n", 1)[1]
            return section.split("```")[0].strip()
        except:
            return None                


        # --- OLLAMA BACKEND ---
        try:
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model_var.get(),
                    "prompt": final_prompt,
                    "stream": False
                }
            )

            llm_text = self.extract_ollama_output(response.json())

            code = self.extract_code_block(llm_text)
            if code:
                send_to_canvas(code, "generated.py")

            return llm_text
            
            

        except Exception as e:
            return f"[ERROR] Ollama failure: {e}"

    def process_training_pass(self, text):
        prompt = (
            REFINEMENT_DIRECTIVE
            + "\n\n---\nTEXT:\n"
            + text
            + "\n---\nREFINED:\n"
        )

        result = self.send_to_backend(prompt)
        return result.strip()
        
       
        
    def clean_for_model(self, prompt_text):
        """
        Remove system scaffolds before sending to the model.
        We want tone guidance, not tone injection.
        """
        cleaned = []
        skip_tags = ["[SessionBootstrap]", "[Agent:", "[Tool:", "[Tone]", "[Framework:"]

        for line in prompt_text.split("\n"):
            if any(line.strip().startswith(tag) for tag in skip_tags):
                continue
            cleaned.append(line)

        return "\n".join(cleaned).strip()        

    def extract_llama_output(self, result):
        if not isinstance(result, dict):
            return str(result)

        # llama.cpp result style:
        # {'choices':[{'text':"..."}]}
        choices = result.get("choices", [])
        if not choices:
            return ""

        text = choices[0].get("text", "")
        return text.strip()


    def extract_ollama_output(self, result):
        # Ollama format:
        # {"response": "..."}
        return result.get("response", "").strip()
        
        
        

    # ==================================================================
    #  TRAINING ENGINE v9
    # ==================================================================
    def open_training_panel(self):
        if hasattr(self, "training_win") and self.training_win.winfo_exists():
            self.training_win.lift()
            return

        self.training_win = tk.Toplevel(self.root)
        self.training_win.title("Training Panel — v10")
        self.training_win.geometry("500x500")
        self.training_win.configure(bg=BG_PANEL)

        tk.Label(
            self.training_win,
            text="📘 Training Panel (v10)",
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

        win.title("MiniTrini DevTools v10")
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
        if text:
            self.backend_process.stdin.write(text + "\n")
            self.backend_process.stdin.flush()
        self.core_input.delete(0, 'end')


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
        # Update dropdown when backend changes
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
            self.llm = Llama(
                model_path=str(model_path),
                n_ctx=2048,
                verbose=False
            )
            self.local_model_loaded = True
        except Exception:
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

    def start(self, text):
        self.active = True
        self.current_cycle = 0
        refined = text.strip()

        self.logs.append(f"[seed]\n{refined}\n")

        while self.active and self.current_cycle < self.max_cycles:

            model_input = refined
            improved = self.app.process_training_pass(model_input).strip()

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
#  SAFE PRESERVED BLOCK — YOUR ALT AGENTS LIST
# ======================================================================
"""
--- UNUSED v9 ALT-AGENTS DEFINITION (PRESERVED FOR YOU) ---

AGENTS = [
    {"name": "Developer", "icon": "💻", "default_tone": "precise", "default_intent": "build"},
    {"name": "Security",  "icon": "🛡️", "default_tone": "formal",  "default_intent": "verify"},
    {"name": "Reasoning", "icon": "🧠", "default_tone": "analytical", "default_intent": "reason"},
    {"name": "Research",  "icon": "🔬", "default_tone": "analytical", "default_intent": "investigate"},
    {"name": "Optimizer", "icon": "⚙️", "default_tone": "precise", "default_intent": "optimize"},
    {"name": "Refactor",  "icon": "🧹", "default_tone": "calm",   "default_intent": "refactor"},
    {"name": "Memory",    "icon": "🧩", "default_tone": "reflective", "default_intent": "retrieve"},
    {"name": "System",    "icon": "🔧", "default_tone": "neutral", "default_intent": "system"},
]
"""


# ======================================================================
#  MAIN EXECUTION
# ======================================================================
if __name__ == "__main__":
    root = tk.Tk()
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