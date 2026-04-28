import hashlib
from pathlib import Path

def compute_hash(file_path: str) -> str:
    """Compute SHA256 hash of the refusal rules file."""
    data = Path(file_path).read_bytes()
    return hashlib.sha256(data).hexdigest()

def update_hash(file_path: str):
    """
    Generate or refresh the refusal_rules.hash file
    so MiniTrini validates refusal logic as intact.
    """
    file_path = Path(file_path)
    hash_value = compute_hash(str(file_path))

    hash_file = file_path.with_suffix(".hash")
    hash_file.write_text(hash_value)

    print(f"[✓] Updated refusal hash:\n    {hash_file}")
