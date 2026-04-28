from pathlib import Path
from sentence_transformers import SentenceTransformer
import numpy as np
import json
import uuid
import re
from collections import Counter
import math

class TriniVectorMemory:

    def __init__(self, memory_dir: Path):
        self.memory_dir = memory_dir
        self.memory_dir.mkdir(parents=True, exist_ok=True)
        self.file_path = self.memory_dir / "vector_index.json"

        self.index_file = self.memory_dir / "vector_index.json"
        self.vector_file = self.memory_dir / "vector_embeddings.npy"

        self.model = SentenceTransformer("all-MiniLM-L6-v2")

        self.memory = []
        self.vectors = np.empty((0, 384))
        self._load()

    def _load(self):
        if not self.file_path.exists():
            self.memory = []
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                self.memory = json.load(f)
        except Exception:
            # corrupted file fallback
            self.memory = []

    def _normalize_for_memory(self, text: str) -> str:
        if not text:
            return ""

        text = text.replace("\r", "")
        text = text.replace("\\n", "\n")

        # strip common model formatting junk
        text = re.sub(r"(^|\n)#{1,6}\s*", r"\1", text)
        text = re.sub(r"(^|\n)---+\s*", r"\1", text)
        text = re.sub(r"(^|\n)TEXT:\s*", r"\1", text, flags=re.IGNORECASE)
        text = re.sub(r"(^|\n)REFINED:\s*", r"\1", text, flags=re.IGNORECASE)

        # collapse noise
        text = re.sub(r"\n{3,}", "\n\n", text)
        text = re.sub(r"[ \t]{2,}", " ", text)

        return text.strip()            
          
        if len(text) < 40:
            return
            
    def _is_corrupted(self, text: str) -> bool:
        if not text or not text.strip():
            return True

        words = re.findall(r"\w+", text.lower())
        if not words:
            return True

        counts = Counter(words)
        most_common_word, freq = counts.most_common(1)[0]

        # dominant repetition
        if freq / len(words) > 0.65:
            return True

        if freq >= 20:
            return True

        # low entropy check
        char_counts = Counter(text)
        total = len(text)
        entropy = -sum((c/total) * math.log2(c/total) for c in char_counts.values())
        if entropy < 2.5:
            return True

        return False
    def _save(self):
        with open(self.index_file, "w") as f:
            json.dump(self.memory, f, indent=2)

        np.save(self.vector_file, self.vectors)

    def add_memory(self, text: str):
        text = self._normalize_for_memory(text)

        if self._is_corrupted(text):
            print("[MemoryGuard] Rejected corrupted output")
            return

        embedding = self.model.encode(text)

        self.memory.append({
            "id": str(uuid.uuid4()),
            "text": text
        })

        if self.vectors.size == 0:
            self.vectors = np.array([embedding])
        else:
            self.vectors = np.vstack([self.vectors, embedding])

        self._save()

        