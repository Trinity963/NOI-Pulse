import hashlib
from pathlib import Path
from llama_cpp import Llama

class CoreModelSocket:
    def __init__(self):
        self.model_path = None
        self.model = None
        self.model_hash = None
        self.status = "🔴 Offline"
        self.error = None

    def load_model(self, model_path):
        self.model_path = Path(model_path)
        if not self.model_path.exists():
            self.error = "Model path does not exist."
            self.status = "🔴 Offline"
            return False

        try:
            self.model_hash = self.compute_hash()
            self.model = Llama(model_path=model_path)
            self.status = "🟢 Ready"
            return True
        except Exception as e:
            self.error = f"Model loading failed: {e}"
            self.model = None
            self.status = "🔴 Offline"
            return False

    def compute_hash(self):
        try:
            sha256 = hashlib.sha256()
            with open(self.model_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256.update(chunk)
            return sha256.hexdigest()
        except Exception as e:
            self.error = f"Hash error: {e}"
            return None

    def chat(self, prompt):
        if self.model:
            return self.model(prompt)
        return "⚠️ Model not loaded."

    def get_status(self):
        return self.status

    def get_model_hash(self):
        return self.model_hash

    def get_error(self):
        return self.error
