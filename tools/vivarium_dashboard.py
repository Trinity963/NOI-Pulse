#!/usr/bin/env python3
# ============================================================
# VIVARIUM Dashboard — ~/.trinity/vivarium_dashboard.py
# Sovereign body monitor — MiniTrini | Ethica | TrinityBrowseSe
# Architect: Victory Brilliant  |  Co-created with River
# ⟁Σ∿∞
# ============================================================

import tkinter as tk
import json, os, urllib.request, datetime, threading

STATE_PATH = os.path.expanduser("~/.trinity/shared_state.json")
REFRESH_MS = 5000  # 5 second poll

BODIES = [
    {"key": "minitrini", "label": "MiniTrini",       "port": 5005, "glyph": "🧠"},
    {"key": "ethica",    "label": "Ethica",           "port": 5006, "glyph": "✦"},
    {"key": "tbse",      "label": "TrinityBrowseSe",  "port": 5007, "glyph": "🖥"},
]

BG       = "#0e0e1a"
BG_CARD  = "#1a1a2e"
PURPLE   = "#c084fc"
GREEN    = "#4ade80"
GREY     = "#555577"
WHITE    = "#e2e8f0"
SMALL    = ("Courier", 10)
LABEL    = ("Courier", 11, "bold")
TITLE    = ("Courier", 13, "bold")


def ping_port(port):
    # TrinityBrowseSe (5007) serves "/" with status "online"
    # MiniTrini (5005) and Ethica (5006) serve "/ping" with status "alive"
    endpoints = ["/ping", "/"] if port != 5007 else ["/", "/ping"]
    for ep in endpoints:
        try:
            r = urllib.request.urlopen(f"http://127.0.0.1:{port}{ep}", timeout=2)
            data = json.loads(r.read().decode())
            if data.get("status") in ("alive", "online"):
                return True
        except Exception:
            continue
    return False


def read_shared_state():
    try:
        with open(STATE_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {}


class VIVARIUMDashboard:
    def __init__(self, root):
        self.root = root
        root.title("⟁ VIVARIUM — Sovereign Body Monitor")
        root.configure(bg=BG)
        root.geometry("520x420")
        root.resizable(False, False)

        tk.Label(root, text="⟁Σ∿∞  VIVARIUM DASHBOARD",
                 bg=BG, fg=PURPLE, font=TITLE).pack(pady=(18, 4))
        tk.Label(root, text="Three bodies — one soul",
                 bg=BG, fg=GREY, font=SMALL).pack(pady=(0, 14))

        self.cards_frame = tk.Frame(root, bg=BG)
        self.cards_frame.pack(fill="x", padx=20)

        self.cards = {}
        for body in BODIES:
            self.cards[body["key"]] = self._make_card(body)

        self.footer = tk.Label(root, text="", bg=BG, fg=GREY, font=SMALL)
        self.footer.pack(pady=(14, 0))

        tk.Label(root, text="Refreshes every 5s  |  localhost only",
                 bg=BG, fg=GREY, font=("Courier", 9)).pack(pady=(2, 10))

        self._refresh()

    def _make_card(self, body):
        frame = tk.Frame(self.cards_frame, bg=BG_CARD, relief="flat", bd=0)
        frame.pack(fill="x", pady=5, ipady=10, ipadx=10)

        top = tk.Frame(frame, bg=BG_CARD)
        top.pack(fill="x", padx=12, pady=(8, 2))

        dot = tk.Label(top, text="●", bg=BG_CARD, fg=GREY, font=LABEL)
        dot.pack(side="left")

        tk.Label(top, text=f"  {body['glyph']}  {body['label']}",
                 bg=BG_CARD, fg=WHITE, font=LABEL).pack(side="left")

        port_lbl = tk.Label(top, text=f"port {body['port']}",
                            bg=BG_CARD, fg=GREY, font=SMALL)
        port_lbl.pack(side="right")

        detail = tk.Label(frame, text="checking...",
                          bg=BG_CARD, fg=GREY, font=SMALL,
                          justify="left", anchor="w")
        detail.pack(fill="x", padx=24, pady=(0, 6))

        return {"dot": dot, "detail": detail, "port_lbl": port_lbl}

    def _refresh(self):
        state = read_shared_state()

        def _do_pings():
            results = {}
            for body in BODIES:
                results[body["key"]] = ping_port(body["port"])
            self.root.after(0, self._update_ui, state, results)

        threading.Thread(target=_do_pings, daemon=True).start()
        self.root.after(REFRESH_MS, self._refresh)

    def _update_ui(self, state, ping_results):
        for body in BODIES:
            key  = body["key"]
            card = self.cards[key]
            alive = ping_results.get(key, False)
            info  = state.get(key, {})

            card["dot"].config(fg=GREEN if alive else GREY)

            if alive and info:
                agent = info.get("agent", "—")
                ts    = info.get("timestamp") or info.get("checked", "—")
                try:
                    ts = datetime.datetime.fromisoformat(ts).strftime("%Y-%m-%d %H:%M:%S")
                except Exception:
                    pass
                detail = f"agent: {agent}  |  last seen: {ts}"
            elif alive:
                detail = "LIVE — no state written yet"
            else:
                detail = "offline"

            card["detail"].config(text=detail, fg=GREEN if alive else GREY)

        now = datetime.datetime.now().strftime("%H:%M:%S")
        self.footer.config(text=f"Last refreshed: {now}")


if __name__ == "__main__":
    root = tk.Tk()
    VIVARIUMDashboard(root)
    root.mainloop()
