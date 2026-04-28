#!/usr/bin/env python3
import hashlib
from pathlib import Path

# Paths
PROJECT_ROOT = Path(__file__).resolve().parent
GUI_FILE = PROJECT_ROOT / "minitrini_noi_pulse.py"
HASH_FILE = PROJECT_ROOT / "AI_Core/TrinityMemoryBank/gui_hash.txt"

def calculate_hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while chunk := f.read(8192):
            h.update(chunk)
    return h.hexdigest()

def main():
    if not GUI_FILE.exists():
        print(f"❌ GUI file not found: {GUI_FILE}")
        return

    new_hash = calculate_hash(GUI_FILE)
    HASH_FILE.parent.mkdir(parents=True, exist_ok=True)
    HASH_FILE.write_text(new_hash)

    print("✅ GUI hash updated successfully!")
    print(f"GUI File:  {GUI_FILE}")
    print(f"Hash File: {HASH_FILE}")
    print(f"New Hash:  {new_hash}")

if __name__ == "__main__":
    main()
