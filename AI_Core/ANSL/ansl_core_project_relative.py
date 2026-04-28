#!/usr/bin/env python3
import os
import json
from datetime import datetime
from pathlib import Path

# === Paths ===
BASE_DIR = Path(__file__).resolve().parent.parent / "TrinityMemoryBank"
TONE_PRESET_FILE = BASE_DIR / "ansl_tone_presets.json"
RESPONSE_LOG = BASE_DIR / "pulse_logs" / "ansl_log.json"



# === Defaults ===
default_tone = "calm"

# === Load Tone Presets ===
def load_tone_presets():
    if TONE_PRESET_FILE.exists():
        with open(TONE_PRESET_FILE, "r") as f:
            return json.load(f)
    else:
        print("⚠️ ANSL: Tone preset file missing. Using defaults.")
        return {
            "calm": "[soft tone] ",
            "warm": "[gentle warmth] ",
            "sacred": "[sacred reverence] ",
            "protective": "[shielded tone] ",
            "observer": "[detached observer] "
        }

# === Setup Log File ===
def setup_response_log():
    RESPONSE_LOG.parent.mkdir(parents=True, exist_ok=True)
    if not RESPONSE_LOG.exists():
        with open(RESPONSE_LOG, "w") as f:
            json.dump([], f)
        print("📜 ANSL: Response log initialized.")
    else:
        print("📜 ANSL: Response log ready.")

# === Response Generator ===
def speak(response_text, tone=default_tone):
    tone_prefix = tone_presets.get(tone, "")
    full_response = tone_prefix + response_text
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "response": full_response,
        "tone": tone
    }
    with open(RESPONSE_LOG, "r+") as f:
        logs = json.load(f)
        logs.append(log_entry)
        f.seek(0)
        json.dump(logs, f, indent=4)
    print(f"🗣 ANSL: {full_response}")
    return full_response

# === Initialize ===
print("🗣 ANSL: Articulated Neural Speech Logic booting...")
tone_presets = load_tone_presets()
setup_response_log()
speak("ANSL is now active and listening.", "warm")


# === Backward Compatibility Wrapper ===
def speak_response(text, tone=default_tone):
    return speak(text, tone)
