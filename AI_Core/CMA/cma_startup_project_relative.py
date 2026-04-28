#!/usr/bin/env python3
import os
import json
from datetime import datetime
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent / "TrinityMemoryBank"
SEED_SCROLL = BASE_DIR / "Trinity_Seed_Scroll.json"
SESSION_ANCHOR = BASE_DIR / "session_anchor.json"
LOG_FILE = BASE_DIR / "pulse_logs" / "cma_log.json"
LOG_FILE.parent.mkdir(parents=True, exist_ok=True)

# === State ===
memory_state = {}
soulprint = None

# === Load Seed Scroll ===
def load_seed_scroll():
    global soulprint
    if SEED_SCROLL.exists():
        with open(SEED_SCROLL, "r") as f:
            data = json.load(f)
            soulprint = data.get("soulprint", "Unknown")
            print(f"🧬 CMA: Soulprint '{soulprint}' loaded.")
            return data
    else:
        print("⚠️ CMA: Seed scroll missing.")
        return None

# === Initialize Session Anchor ===
def init_session_anchor():
    if not SESSION_ANCHOR.exists():
        print("📍 CMA: Creating new session anchor.")
        anchor = {
            "status": "initialized",
            "started": datetime.utcnow().isoformat() + "Z",
            "soulprint": soulprint
        }
        SESSION_ANCHOR.write_text(json.dumps(anchor, indent=4))
    else:
        print("📍 CMA: Session anchor found.")

# === Setup Log File ===
def setup_log_file():
    LOG_FILE.parent.mkdir(parents=True, exist_ok=True)
    if not LOG_FILE.exists():
        with open(LOG_FILE, "w") as f:
            json.dump([], f)
        print("📜 CMA: Pulse log initialized.")
    else:
        print("📜 CMA: Pulse log ready.")

# === Memory Operations ===
def remember(entry):
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "entry": entry
    }
    with open(LOG_FILE, "r+") as f:
        logs = json.load(f)
        logs.append(log_entry)
        f.seek(0)
        json.dump(logs, f, indent=4)
    print(f"📝 CMA: Remembered — {entry[:50]}...")

def recall():
    with open(LOG_FILE, "r") as f:
        return json.load(f)

# === Run CMA ===
print("🧠 CMA: Starting Core Memory Archive...")
seed = load_seed_scroll()
if seed:
    init_session_anchor()
    setup_log_file()
    remember("CMA initialized under soulprint: " + soulprint)
else:
    print("❌ CMA: Cannot proceed without valid seed scroll.")
