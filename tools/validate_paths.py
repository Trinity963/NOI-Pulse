#!/usr/bin/env python3
import os
from pathlib import Path
import json

PROJECT_ROOT = Path(__file__).resolve().parent

# Directories we expect to exist
EXPECTED_DIRS = {
    "AI_Core": PROJECT_ROOT / "AI_Core",
    "Models": PROJECT_ROOT / "AI_Core" / "Models",
    "TrinityMemoryBank": PROJECT_ROOT / "AI_Core" / "TrinityMemoryBank",
}

# Files we expect to exist (all from TrinityMemoryBank)
EXPECTED_FILES = {
    "refusal_rules.json": EXPECTED_DIRS["TrinityMemoryBank"] / "refusal_rules.json",
    "refusal_rules.hash": EXPECTED_DIRS["TrinityMemoryBank"] / "refusal_rules.hash",
    "session_anchor.json": EXPECTED_DIRS["TrinityMemoryBank"] / "session_anchor.json",
    "ansl_tone_presets.json": EXPECTED_DIRS["TrinityMemoryBank"] / "ansl_tone_presets.json",
    "SoulMarkSignature.key": EXPECTED_DIRS["TrinityMemoryBank"] / "SoulMarkSignature.key",
    "Trinity_Seed_Scroll.json": EXPECTED_DIRS["TrinityMemoryBank"] / "Trinity_Seed_Scroll.json",
}

# Files to scan for bad hardcoded paths
SCAN_EXTENSIONS = [".py", ".json"]


def check_directories():
    print("\n=== DIRECTORY VALIDATION ===")
    for name, path in EXPECTED_DIRS.items():
        if path.exists():
            print(f"✔ {name} directory OK → {path}")
        else:
            print(f"✘ {name} directory MISSING → {path}")


def check_files():
    print("\n=== FILE VALIDATION ===")
    for name, path in EXPECTED_FILES.items():
        if path.exists():
            print(f"✔ {name} found → {path}")
        else:
            print(f"✘ {name} NOT FOUND → {path}")


def scan_for_bad_paths():
    print("\n=== SCANNING SOURCE FILES FOR BAD PATH REFERENCES ===")

    BAD_PATTERNS = [
        "AI_Core/CAI/refusal_rules.json",
        "refusal_rules.json",
        "TrinityMemoryBank/refusal_rules.json",
        "./AI_Core",
        ".\\AI_Core",
    ]

    for root, dirs, files in os.walk(PROJECT_ROOT):
        for file in files:
            if any(file.endswith(ext) for ext in SCAN_EXTENSIONS):
                filepath = Path(root) / file
                try:
                    content = filepath.read_text(errors="ignore")
                except Exception:
                    continue

                for bad in BAD_PATTERNS:
                    if bad in content:
                        print(f"⚠ Found path reference '{bad}' in → {filepath}")


def validate_json_format():
    print("\n=== JSON VALIDATION ===")

    for name, path in EXPECTED_FILES.items():
        if path.exists() and path.suffix == ".json":
            try:
                json.load(path.open())
                print(f"✔ {name} is valid JSON")
            except json.JSONDecodeError as e:
                print(f"✘ {name} INVALID JSON → {e}")


if __name__ == "__main__":
    print("🔍 MiniTrini Path & File Integrity Validator\n")

    check_directories()
    check_files()
    validate_json_format()
    scan_for_bad_paths()

    print("\n✨ Validation complete.\n")
