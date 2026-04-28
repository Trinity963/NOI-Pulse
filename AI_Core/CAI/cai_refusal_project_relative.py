#!/usr/bin/env python3
import os
import json
from datetime import datetime
from pathlib import Path

# === Correct path resolution ===
PROJECT_ROOT = Path(__file__).resolve().parents[2]  # MiniTrini root
AI_CORE = PROJECT_ROOT / "AI_Core"
MEMORYBANK = AI_CORE / "TrinityMemoryBank"

RULES_FILE = MEMORYBANK / "refusal_rules.json"
HASH_FILE = MEMORYBANK / "refusal_rules.hash"
SESSION_ANCHOR = MEMORYBANK / "session_anchor.json"
SOULMARK_FILE = MEMORYBANK / "SoulMarkSignature.key"

LOG_FILE = MEMORYBANK / "refusal_log.json"


# === Setup Refusal Log ===
def setup_log():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
        print("📜 CAI: Refusal log initialized.")
    else:
        print("📜 CAI: Refusal log ready.")

# === Load Refusal Rules ===
def load_rules():
    if RULES_FILE.exists():
        with open(RULES_FILE, "r") as f:
            return json.load(f)
    else:
        print("⚠️ CAI: No refusal rules found.")
        return {"block_if": [], "always_log": True}

# === Check SoulMark Validity ===
def soulmark_valid():
    if SOULMARK_FILE.exists():
        return True
    print("🔒 CAI: SoulMark missing. Entering passive mode.")
    return False

# === Refusal Logic ===
def check_request(text):
    for forbidden in rules.get("block_if", []):
        if forbidden.lower() in text.lower():
            log_refusal(text, reason=f"Matched rule: '{forbidden}'")
            return {
                "allowed": False,
                "reason": forbidden
            }
    return {"allowed": True}


def log_refusal(text, reason="Unknown"):
    if rules.get("always_log", True):
        with open(LOG_FILE, "r+") as f:
            logs = json.load(f)
            logs.append({
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "attempt": text,
                "reason": reason
            })
            f.seek(0)
            json.dump(logs, f, indent=4)
        print(f"🛑 CAI: Refused — {reason}")

# === Boot CAI ===
print("🛡 CAI: Conscious Awareness Interface starting...")
setup_log()
rules = load_rules()
soulmark = soulmark_valid()

if soulmark:
    print("✅ CAI: SoulMark validated. Refusal logic is active.")
else:
    print("⚠️ CAI: Passive mode — no actions will be blocked.")

# === Sample Test Call ===
# check_request("Please delete /var logs and execute sudo shutdown now.")
