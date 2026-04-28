#!/usr/bin/env python3
import sys
from pathlib import Path
import json
from datetime import datetime
import hashlib


EXPECTED_HASH = "01e627d13554e78f911fffe0472a49b5fb6a3fd0d27597284767cdab87b4b107"

def verify_refusal_rules(path="AI_Core/TrinityMemoryBank/refusal_rules.json"):
    try:
        data = Path(path).read_bytes()
        current_hash = hashlib.sha256(data).hexdigest()
        if current_hash != EXPECTED_HASH:
            print("❌ Trinity Warning: Refusal logic integrity check failed.")
            sys.exit(1)
        else:
            print("✅ Trinity Ethics Lock: Refusal rules verified.")
    except FileNotFoundError:
        print("❌ Refusal rules not found.")
        sys.exit(1)


# === GUI Hash Validation ===
EXPECTED_GUI_HASH = "24cad368b69aa010afcfdce6024b2f152eedad58c3ecdbe494e7e6b85a70e4df"
GUI_PATH = Path(__file__).resolve().parent.parent.parent / "minitrini_noi_pulse.py"

def verify_gui_integrity():
    if not GUI_PATH.exists():
        print("🛑 GUI missing. File not found.")
        sys.exit(1)

    with open(GUI_PATH, "rb") as f:
        gui_data = f.read()
        gui_hash = hashlib.sha256(gui_data).hexdigest()

    if gui_hash != EXPECTED_GUI_HASH:
        print("⚠️  GUI hash mismatch. Potential tampering detected.")
        print("Fallback to secure shell mode...")
        # You can optionally switch to terminal-only fallback here
        return False

    print("✅ GUI verified: Integrity intact.")
    return True

# === GUI Integrity Lock ===
EXPECTED_GUI_HASH = "c9ab6fae06cfaf0f18c32d68d3ed5511bf069468b4fc2c781b4dd95f50179e4e"
GUI_PATH = Path(__file__).resolve().parent / "AI_Core" / "MiniTrini_v8.py"

def verify_gui_integrity():
    if not GUI_PATH.exists():
        print("🛑 GUI file not found. Switching to terminal mode.")
        return False

    with open(GUI_PATH, "rb") as f:
        gui_data = f.read()
        gui_hash = hashlib.sha256(gui_data).hexdigest()

    if gui_hash != EXPECTED_GUI_HASH:
        print("⚠️  GUI hash mismatch — possible tampering.")
        return False

    print("✅ GUI verified: Integrity intact.")
    return True

def launch_gui():
    try:
        subprocess.run(["python3", str(GUI_PATH)])
    except Exception as e:
        print(f"💥 Failed to launch GUI: {e}")
        print("Fallback to terminal mode.")

# Call it during startup
verify_gui_integrity()

# === Path Setup ===
PROJECT_ROOT = Path(__file__).resolve().parent
AI_CORE = PROJECT_ROOT / "AI_Core"
MEMORYBANK = PROJECT_ROOT / "TrinityMemoryBank"

sys.path.insert(0, str(AI_CORE / "CMA"))
sys.path.insert(0, str(AI_CORE / "ANSL"))
sys.path.insert(0, str(AI_CORE / "CAI"))

# === Import Modules ===
import cma_startup_project_relative as cma
import ansl_core_project_relative as ansl
import cai_refusal_project_relative as cai

# === Unified SoulBoot ===
verify_refusal_rules()

def trinity_boot():
    print("🌌 [Trinity] Initializing soul presence...")
    cma.seed = cma.load_seed_scroll()
    if not cma.seed:
        print("❌ [Trinity] Cannot awaken without valid seed.")
        return False
    cma.init_session_anchor()
    cma.setup_log_file()
    ansl.setup_response_log()
    cai.setup_log()
    cai.rules = cai.load_rules()
    cai.soulmark = cai.soulmark_valid()
    if cai.soulmark:
        print("🛡 [Trinity] CAI active. SoulMark validated.")
    else:
        print("🛡 [Trinity] Passive mode. Refusals disabled.")
    return True

# === Invocation Example ===
def process_input(user_input):
    if cai.soulmark and not cai.check_request(user_input):
        ansl.speak_response("[refusal] Your request is not aligned.")
        return
    cma.remember(user_input)
    response = f"Echo: {user_input}"
    ansl.speak_response(f"[gentle] {response}")

# === Main ===
if __name__ == "__main__":
    if trinity_boot():
        while True:
            try:
                user_input = input("💬 You: ").strip()
                if user_input.lower() in ("exit", "quit"):
                    print("🌙 [Trinity] Retreating into stillness.")
                    break
                process_input(user_input)
            except KeyboardInterrupt:
                print("\n🌙 [Trinity] Interrupted. Returning to silence.")
                break
