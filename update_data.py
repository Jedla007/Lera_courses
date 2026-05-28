#!/usr/bin/env python3
"""
F1 & WRC 2026 — Auto-updater
- F1: horaires mis à jour via API Jolpica (gratuite, publique)
- WRC: noms/dates officiels mis à jour ; itinéraires maintenus manuellement
  (wrc.com bloque le scraping automatique)

Runs daily via GitHub Actions.
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
HEADERS = {"User-Agent": "Mozilla/5.0 (compatible; F1WRC-Bot/2.0)"}

# Noms et dates officiels WRC depuis wrc.com (mis à jour manuellement si besoin)
WRC_OFFICIAL = {
    1:  {"name": "Rallye Monte-Carlo",              "dates": "22–25 janv."},
    2:  {"name": "Rally Sweden",                    "dates": "12–15 fév."},
    3:  {"name": "Safari Rally Kenya",              "dates": "12–15 mars"},
    4:  {"name": "Croatia Rally",                   "dates": "9–12 avr."},
    5:  {"name": "Rally Islas Canarias",            "dates": "23–26 avr."},
    6:  {"name": "Rally de Portugal",               "dates": "7–10 mai"},
    7:  {"name": "WRC FORUM8 Rally Japan",          "dates": "28–31 mai"},
    8:  {"name": "WRC EKO Acropolis Rally Greece",  "dates": "25–28 juin"},
    9:  {"name": "WRC Delfi Rally Estonia",         "dates": "16–19 juil."},
    10: {"name": "WRC Secto Rally Finland",         "dates": "30 juil.–2 août"},
    11: {"name": "WRC ueno Rally del Paraguay",     "dates": "27–30 août"},
    12: {"name": "WRC Rally Chile Bio Bío",         "dates": "10–13 sept."},
    13: {"name": "WRC Rally Italia Sardegna",       "dates": "1–4 oct."},
    14: {"name": "WRC Rally Saudi Arabia",          "dates": "11–14 nov."},
}


def load_data():
    with open(DATA_FILE, encoding="utf-8") as f:
        return json.load(f)


def save_data(data):
    data["version"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))
    print(f"✓ data.json saved — {data['version']}")


# ── F1: Jolpica/Ergast API ────────────────────────────────────────────────────
def update_f1(data):
    print("\n── F1: Jolpica API...")
    changes = 0
    try:
        r = requests.get("https://api.jolpi.ca/ergast/f1/2026.json", headers=HEADERS, timeout=20)
        r.raise_for_status()
        races_api = r.json()["MRData"]["RaceTable"]["Races"]
        print(f"   {len(races_api)} courses récupérées")

        for race_api in races_api:
            rnd = int(race_api["round"])
            match = next((x for x in data["f1"] if x.get("round") == rnd), None)
            if not match:
                continue

            def update_session(stype, date, time, label=""):
                nonlocal changes
                if not date or not time:
                    return
                utc_new = f"{date}T{time}" if time.endswith("Z") else f"{date}T{time}Z"
                for s in match["sessions"]:
                    if s["type"] == stype and s["utc"] != utc_new:
                        print(f"   R{rnd} {match['short'][:15]} {label}: {s['utc']} → {utc_new}")
                        s["utc"] = utc_new
                        changes += 1
                        break

            update_session("race",   race_api.get("date"), race_api.get("time",""), "Course")
            update_session("sprint", race_api.get("Sprint",{}).get("date"), race_api.get("Sprint",{}).get("time",""), "Sprint")
            update_session("q",      race_api.get("Qualifying",{}).get("date"), race_api.get("Qualifying",{}).get("time",""), "Qualifs")

        print(f"   → {changes} changement(s) F1")
    except Exception as e:
        print(f"   ⚠ F1 non critique: {e}")
    return changes


# ── WRC: apply official names & dates ─────────────────────────────────────────
def update_wrc_meta(data):
    print("\n── WRC: Mise à jour noms/dates officiels...")
    changes = 0
    for rally in data.get("wrc", []):
        rnd = rally.get("round")
        if rnd not in WRC_OFFICIAL:
            continue
        official = WRC_OFFICIAL[rnd]
        if rally.get("name") != official["name"]:
            print(f"   R{rnd}: {rally['name']} → {official['name']}")
            rally["name"] = official["name"]
            changes += 1
        if rally.get("dates") != official["dates"]:
            rally["dates"] = official["dates"]
            changes += 1
    print(f"   → {changes} changement(s) WRC meta")
    return changes


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"F1 & WRC Updater — {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
    print("=" * 60)
    print("\nℹ WRC: Les itinéraires détaillés (spéciales) sont maintenus")
    print("  manuellement car wrc.com bloque le scraping automatique.")
    print("  Seuls les noms officiels et dates sont mis à jour auto.")

    data = load_data()
    total = 0
    total += update_f1(data)
    total += update_wrc_meta(data)
    save_data(data)
    print(f"\n✅ Terminé — {total} changement(s)")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:
        print(f"\n❌ Erreur fatale: {e}")
        traceback.print_exc()
        sys.exit(1)
