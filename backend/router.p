import requests
import re
import threading
from TrinityCanvas import open_canvas, send_to_canvas

try:
    from engine.learning import RecursiveLearningEngine
except Exception:
    RecursiveLearningEngine = None


class BackendRouter:
    def __init__(self, app):
        self.app = app

    def send(self, prompt_text):
        print("ROUTER HIT")

        if self.app.backend_mode == "local":
            if not getattr(self.app, "llm", None):
                return "[ERROR] Local LLM not loaded."

        cleaned_input = self.clean_for_model(prompt_text)

        state = getattr(self.app, "state", {}) or {}
        agent = state.get("agent", "")
        tool = state.get("tool", "")

        final_prompt = self.build_prompt(agent, tool, cleaned_input)

        if self.app.backend_mode == "local":
            print("=== FINAL PROMPT SENT TO TRINITY ===")
            print(repr(final_prompt))
            print("=================================")

            try:
                with self.app.llm_lock:
                    result = self.app.llm(
                        final_prompt,
                        max_tokens=getattr(self.app, "max_tokens", 360),
                        temperature=getattr(self.app, "temperature", 0.3),
                        top_p=getattr(self.app, "top_p", 0.9),
                        repeat_penalty=1.1
                    )

                text = self.extract_local_text(result)
                cleaned = self.strip_think_tags(text)
                cleaned = cleaned.replace("```python", "").replace("```", "").strip()

                print("CLEANED:", repr(cleaned))

                try:
                    if agent == "Research" and cleaned and len(cleaned) > 120:
                        print("AUTO TRAINING TRIGGER")

                        if RecursiveLearningEngine is not None:
                            engine = RecursiveLearningEngine(self.app)

                            def run_auto_training():
                                try:
                                    result = engine.start(cleaned)
                                    if result and hasattr(self.app, "training_memory"):
                                        self.app.training_memory.add_memory(result)
                                except Exception as e:
                                    print("AUTO TRAIN ERROR:", e)

                            threading.Thread(target=run_auto_training, daemon=True).start()
                        else:
                            print("AUTO TRAIN SKIPPED: RecursiveLearningEngine unavailable")

                except Exception as e:
                    print("AUTO TRAIN HOOK ERROR:", e)

                try:
                    if hasattr(self.app, "vector_memory") and self.app.vector_memory is not None:
                        mem = cleaned.strip()

                        print("MEMHOOK agent =", repr(agent))
                        print("MEMHOOK mem =", repr(mem[:120]))

                        if agent == "Trini" and mem and not mem.startswith("[ERROR]") and len(mem) > 20:
                            print("MEMHOOK saving...")
                            self.app.vector_memory.add_memory(mem)

                except Exception as e:
                    print("MEMORY HOOK FAIL:", e)

                try:
                    if tool == "Code" or "def " in cleaned:
                        self.app.root.after(
                            0,
                            lambda: (
                                open_canvas(),
                                send_to_canvas(cleaned, "generated.py")
                            )
                        )
                except Exception as e:
                    print("CANVAS HOOK FAIL:", e)

                return cleaned if cleaned else "[ERROR] Local model returned empty output."

            except Exception as e:
                return f"[ERROR] Local generation failed: {e}"

        elif self.app.backend_mode == "ollama":
            try:
                ollama_model = getattr(self.app, "ollama_model_name", None)
                if not ollama_model:
                    model_var = getattr(self.app, "model_var", None)
                    if model_var is not None:
                        try:
                            ollama_model = model_var.get()
                        except Exception:
                            ollama_model = None

                if not ollama_model:
                    return "[ERROR] No Ollama model configured."

                response = requests.post(
                    "http://localhost:11434/api/generate",
                    json={
                        "model": ollama_model,
                        "prompt": final_prompt,
                        "stream": False,
                        "options": {
                            "temperature": getattr(self.app, "temperature", 0.3),
                            "top_p": getattr(self.app, "top_p", 0.9),
                            "num_predict": getattr(self.app, "max_tokens", 360)
                        }
                    },
                    timeout=(5, 120)
                )
                response.raise_for_status()

                data = response.json()
                content = data.get("response", "")
                cleaned = self.strip_think_tags(content)

                print("CLEANED:", repr(cleaned))

                try:
                    if tool == "Code" or "def " in cleaned:
                        self.app.root.after(
                            0,
                            lambda: (
                                open_canvas(),
                                send_to_canvas(cleaned, "generated.py")
                            )
                        )
                except Exception as e:
                    print("CANVAS HOOK FAIL:", e)

                return cleaned if cleaned else content.strip()

            except Exception as e:
                return f"[ERROR] Ollama failure: {e}"

        return "[ERROR] Invalid backend mode."

    def build_prompt(self, agent, tool, cleaned_input):
        try:
            if hasattr(self.app, "build_backend_prompt") and callable(self.app.build_backend_prompt):
                return self.app.build_backend_prompt(agent, tool, cleaned_input)
        except Exception as e:
            print("build_backend_prompt failed:", e)

        parts = []
        if agent:
            parts.append(f"[Agent: {agent}]")
        if tool:
            parts.append(f"[Tool: {tool}]")
        parts.append(cleaned_input)
        return "\n\n".join(parts).strip()

    def clean_for_model(self, prompt_text):
        cleaned = []
        skip_tags = [
            "[SessionBootstrap]",
            "[Agent:",
            "[Tool:",
            "[Tone]",
            "[Framework:"
        ]

        for line in str(prompt_text).split("\n"):
            if any(line.strip().startswith(tag) for tag in skip_tags):
                continue
            cleaned.append(line)

        return "\n".join(cleaned).strip()

    def extract_chat_content(self, result):
        if not isinstance(result, dict):
            return str(result)

        choices = result.get("choices", [])
        if not choices:
            return ""

        message = choices[0].get("message", {})
        content = message.get("content", "")

        return content.strip()

    def extract_local_text(self, result):
        if result is None:
            return ""

        if isinstance(result, str):
            return result.strip()

        if isinstance(result, dict):
            choices = result.get("choices", [])
            if choices:
                choice0 = choices[0]
                if isinstance(choice0, dict):
                    if "text" in choice0:
                        return str(choice0.get("text", "")).strip()
                    message = choice0.get("message", {})
                    if isinstance(message, dict):
                        return str(message.get("content", "")).strip()

        return str(result).strip()

    def strip_think_tags(self, text):
        if not text:
            return ""

        cleaned = re.sub(
            r"<think>.*?</think>",
            "",
            str(text),
            flags=re.DOTALL
        ).strip()

        return cleaned if cleaned else str(text).strip()