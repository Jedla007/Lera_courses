#!/usr/bin/env python3
"""
F1 & WRC 2026 — Auto-updater (robuste)
Tourne chaque nuit via GitHub Actions.
"""

import json, sys, traceback
from datetime import datetime, timezone
from pathlib import Path

try:
    import requests
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "requests", "-q"])
    import requests

DATA_FILE = Path(__file__).parent / "data.json"
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; F1WRC-Bot/1.0)"}

def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)

def save_data(data):
    data["version"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(',', ':'))
    print(f"✓ data.json sauvegardé — {data['version']}")

def update_f1(data):
    print("\n── F1: Jolpica/Ergast API...")
    changes = 0
    try:
        url = "https://api.jolpi.ca/ergast/f1/2026.json"
        r = requests.get(url, headers=HEADERS, timeout=20)
        r.raise_for_status()
        races_api = r.json()["MRData"]["RaceTable"]["Races"]
        print(f"   {len(races_api)} courses récupérées")

        for race_api in races_api:
            rnd = int(race_api["round"])
            match = next((x for x in data["f1"] if x.get("round") == rnd), None)
            if not match:
                continue

            # Course principale
            d = race_api.get("date","")
            t = race_api.get("time","")
            if d and t:
                utc_new = f"{d}T{t}" if t.endswith("Z") else f"{d}T{t}Z"
                for s in match["sessions"]:
                    if s["type"] == "race" and s["utc"] != utc_new:
                        print(f"   R{rnd} Course: {s['utc']} → {utc_new}")
                        s["utc"] = utc_new
                        changes += 1

            # Sprint
            sprint = race_api.get("Sprint", {})
            sd, st = sprint.get("date",""), sprint.get("time","")
            if sd and st:
                utc_new = f"{sd}T{st}" if st.endswith("Z") else f"{sd}T{st}Z"
                for s in match["sessions"]:
                    if s["type"] == "sprint" and s["utc"] != utc_new:
                        print(f"   R{rnd} Sprint: {s['utc']} → {utc_new}")
                        s["utc"] = utc_new
                        changes += 1

            # Qualifications
            q = race_api.get("Qualifying", {})
            qd, qt = q.get("date",""), q.get("time","")
            if qd and qt:
                utc_new = f"{qd}T{qt}" if qt.endswith("Z") else f"{qd}T{qt}Z"
                for s in match["sessions"]:
                    if s["type"] == "q" and "Sprint" not in s["label"] and s["utc"] != utc_new:
                        print(f"   R{rnd} Qualifs: {s['utc']} → {utc_new}")
                        s["utc"] = utc_new
                        changes += 1
                        break

    except Exception as e:
        print(f"   ⚠ F1 update non critique: {e}")
    
    print(f"   → {changes} changement(s)")
    return changes

def main():
    print("=" * 55)
    print(f"F1 & WRC Updater — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 55)

    data = load_data()
    total = 0

    total += update_f1(data)
    # WRC: pas d'API publique fiable, les données sont maintenues manuellement

    save_data(data)
    print(f"\n✅ Terminé — {total} changement(s) au total")
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        traceback.print_exc()
        sys.exit(1)
