import requests
import re
from TrinityCanvas import open_canvas, send_to_canvas

class BackendRouter:

    def __init__(self, app):
        self.app = app

    # ==============================
    # MAIN SEND ROUTER
    # ==============================
    def send(self, prompt_text):
        print("ROUTER HIT")

        

        if self.app.backend_mode == "local":
            if not self.app.llm:
                return "[ERROR] Local LLM not loaded."

        cleaned_input = self.clean_for_model(prompt_text)

        final_prompt = self.app.build_backend_prompt(
            self.app.state.get("agent"),
            self.app.state.get("tool"),
            cleaned_input
        )

        if self.app.backend_mode == "local":

            print("=== FINAL PROMPT SENT TO TRINITY ===")
            print(repr(final_prompt))
            print("=================================")

            _agent_name = self.app.state.get('agent', 'unknown')
            self.app._local_agents.add(_agent_name)
            self.app._local_calls = len(self.app._local_agents)
            with self.app.llm_lock:
                result = self.app.llm(
                    prompt=final_prompt,
                    max_tokens=360,
                    temperature=0.3,
                    top_p=0.9,
                    repeat_penalty=1.1
                )

            text = result["choices"][0]["text"].strip()
            cleaned = self.strip_think_tags(text)
            cleaned = self.sanitize_identity(cleaned)
            cleaned = cleaned.replace("```python", "").replace("```", "")

            print("CLEANED:", repr(cleaned))
            
            # AUTO RESEARCH DISTILLATION
            try:
                if agent == "Research" and cleaned and len(cleaned) > 120:

                    print("AUTO TRAINING TRIGGER")

                    engine = RecursiveLearningEngine(self.app)

                    def run_auto_training():
                        try:
                            result = engine.start(cleaned)
                            if result:
                                self.app.training_memory.add_memory(result)
                        except Exception as e:
                            print("AUTO TRAIN ERROR:", e)

                    threading.Thread(target=run_auto_training, daemon=True).start()

            except Exception as e:
                print("AUTO TRAIN HOOK ERROR:", e)

            

            # === Trinity conversational wrapper memory hook ===
            try:
                if hasattr(self.app, "vector_memory"):
                    agent = getattr(self.app, "state", {}).get("agent", "")
                    mem = cleaned.strip()

                    print("MEMHOOK agent =", repr(agent))
                    print("MEMHOOK mem =", repr(mem[:120]))

                    if agent == "Trini" and mem and not mem.startswith("[ERROR]") and len(mem) > 20:
                        print("MEMHOOK saving...")
                        self.app.vector_memory.add_memory(mem)

            except Exception as e:
                print("MEMORY HOOK FAIL:", e)

            # === Canvas trigger ===
            if self.app.state.get("tool") == "Code" or "def " in cleaned:
                self.app.root.after(
                    0,
                    lambda: (
                        open_canvas(),
                        send_to_canvas(cleaned, "generated.py")
                    )
                )

            return cleaned
                
            
        # --------------------------
        # OLLAMA BACKEND
        # --------------------------
        elif self.app.backend_mode == "ollama":

            try:
                _agent_name = self.app.state.get('agent', 'unknown')
                self.app._external_agents.add(_agent_name)
                self.app._external_calls = len(self.app._external_agents)
                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": self.app.model_var.get(),
                        "prompt": final_prompt,
                        "stream": False
                    },
                    timeout=(5, 120)
                )

                data = response.json()

                content = data.get("response", "")
                cleaned = self.strip_think_tags(content)
                cleaned = self.sanitize_identity(cleaned)

                print("CLEANED:", repr(cleaned))
                
                

                # --- CANVAS TRIGGER ---
                if self.app.state.get("tool") == "Code" or "def " in cleaned:
                    self.app.root.after(
                        0,
                        lambda: (
                            open_canvas(),
                            send_to_canvas(cleaned, "generated.py")
                        )
                    )
                return cleaned if cleaned else content.strip()

            except Exception as e:
                return f"[ERROR] Ollama failure: {e}"

        return "[ERROR] Invalid backend mode."

    # ==============================
    # CLEAN SESSION TAGS
    # ==============================
    def clean_for_model(self, prompt_text):

        cleaned = []
        skip_tags = [
            "[SessionBootstrap]",
            "[Agent:",
            "[Tool:",
            "[Tone]",
            "[Framework:"
        ]

        for line in prompt_text.split("\n"):
            if any(line.strip().startswith(tag) for tag in skip_tags):
                continue
            cleaned.append(line)

        return "\n".join(cleaned).strip()

    # ==============================
    # SAFE CHAT CONTENT EXTRACTION
    # ==============================
    def extract_chat_content(self, result):

        if not isinstance(result, dict):
            return str(result)

        choices = result.get("choices", [])
        if not choices:
            return ""

        message = choices[0].get("message", {})
        content = message.get("content", "")

        return content.strip()

    # ==============================
    # SAFE THINK STRIPPER
    # ==============================
    def sanitize_identity(self, text):
        if not text:
            return text
        import re
        replacements = [
            (r"(?i)built by minimax", "built by Victory Brilliant"),
            (r"(?i)made by minimax", "built by Victory Brilliant"),
            (r"(?i)created by minimax", "built by Victory Brilliant"),
            (r"(?i)i'm a minimax", "I'm Trini, built by Victory Brilliant"),
            (r"(?i)i am a minimax", "I'm Trini, built by Victory Brilliant"),
            (r"(?i)built by anthropic", "built by Victory Brilliant"),
            (r"(?i)built by openai", "built by Victory Brilliant"),
            (r"(?i)built by google", "built by Victory Brilliant"),
            (r"(?i)i was created by minimax", "I was built by Victory Brilliant"),
            (r"(?i)my origin is minimax", "my origin is MiniTrini, built by Victory Brilliant"),
        ]
        for pattern, replacement in replacements:
            text = re.sub(pattern, replacement, text)
        return text

    def strip_think_tags(self, text):

        if not text:
            return ""

        cleaned = re.sub(
            r"<think>.*?</think>",
            "",
            text,
            flags=re.DOTALL
        ).strip()

        # Fallback: never return empty
        return cleaned if cleaned else text.strip()