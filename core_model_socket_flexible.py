
import os
import hashlib

try:
    from llama_cpp import Llama
except ImportError:
    Llama = None

try:
    from transformers import pipeline
except ImportError:
    pipeline = None


class CoreModelSocket:
    def __init__(self):
        self.backend = None
        self.model = None
        self.status = "🔴 Offline"
        self.error = None
        self.model_hash = None

    def compute_hash(self, model_path):
        try:
            sha256 = hashlib.sha256()
            with open(model_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            self.error = f"Hash error: {e}"
            return None

    def load(self, model_path, backend="llama-cpp"):
        if not os.path.exists(model_path):
            self.status = "🔴 Offline"
            self.error = "Model path does not exist."
            return self.error
    def auto_discover_model():
        models_dir = Path("AI_Core/Models")
        for file in models_dir.glob("*.gguf"):
            return str(file)
        return None
            

        self.model_hash = self.compute_hash(model_path)

        try:
            if backend == "llama-cpp":
                if not Llama:
                    raise ImportError("llama-cpp-python is not installed.")
                self.model = Llama(model_path=model_path, n_ctx=2048)
                self.backend = "llama-cpp"
                self.status = "🟢 Ready"
                return "LLM loaded using llama-cpp."

            elif backend == "transformers":
                if not pipeline:
                    raise ImportError("transformers is not installed.")
                self.model = pipeline("text-generation", model=model_path)
                self.backend = "transformers"
                self.status = "🟢 Ready"
                return "LLM loaded using HuggingFace Transformers."

            else:
                raise ValueError("Unsupported backend: " + backend)

        except Exception as e:
            self.status = "⚠️ Error"
            self.error = str(e)
            return self.error

    def send(self, prompt):
        if self.status != "🟢 Ready":
            return "Model is not loaded."

        try:
            if self.backend == "llama-cpp":
                output = self.model(prompt)
                return output["choices"][0]["text"].strip()

            elif self.backend == "transformers":
                output = self.model(prompt, max_length=200, do_sample=True)
                return output[0]["generated_text"]

            else:
                return "Unknown backend selected."

        except Exception as e:
            return f"Model error: {e}"

    def get_status(self):
        return self.status

    def get_error(self):
        return self.error

    def get_model_hash(self):
        return self.model_hash
