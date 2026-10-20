"""Construit week/SCHEDULE.json : 1 reel 3D (13h00) + 1 visite guidée (20h00) par jour, légendes contrôlées (check_copy, UTM).
  python tools/build_week.py 2026-10-20
"""
import json
import sys
from datetime import date, timedelta
from pathlib import Path

from wooplans.guardrails import check_copy
from wooplans.image_posts import load_plans
from wooplans.reel_posts import captions, problems
from wooplans.settings import OFFER_PRICE_FCFA, ROOT
from wooplans.reel3d import fcfa
from wooplans.utm import build_link

REELS = ["V3-001", "V4-004", "D4-006", "V4-010", "D5-016", "V3-025", "D4-026"]
TOURS = ["V2-2CH-01", "V3-3CH-01", "V3-3CH-02", "V4-4CH-01", "V4-4CH-02", "V5-5CH-01"]
TAGS = {"facebook": "#plandemaison #villa #maison #construction #architecture #Afrique",
        "youtube": "#plandemaison #villa #maison #construction", "tiktok": "#plandemaison #villa #maison #Afrique #WooPlans"}


def tour_caps(job: str) -> dict:
    meta = json.loads((ROOT / "visite_plan/jobs" / job / "meta.json").read_text(encoding="utf-8"))
    n = meta["band"].split("·")[1].split()[0]
    rooms = [s["name"].lower() for s in json.loads((ROOT / "visite_plan/jobs" / job / "voix/script.json").read_text(encoding="utf-8"))]
    rooms = [r for r in rooms if r not in ("hall", "cta", "wc")]
    rooms = [("salle de bain" if r == "sdb" else r) for r in rooms if not r.startswith("chambre")] + [f"{n} chambres dont une chambre parentale"]
    txt = ", ".join(rooms[:-1]) + " et " + rooms[-1] if len(rooms) > 1 else rooms[0]
    out = {}
    for plat in ("facebook", "youtube", "tiktok"):
        link = build_link(plat, "A", job)
        out[plat] = {"caption": f"Visite guidée d'une villa {n} chambres 🏡\n{txt[0].upper() + txt[1:]}.\n\n"
                                f"📘 Envie d'autres plans ? Catalogue Premium : plans complets + devis détaillés, prix actuel : {fcfa(OFFER_PRICE_FCFA)} FCFA\n"
                                f"👉 {link}\n\n{TAGS[plat]}"}
    out["youtube"] = {"title": f"Visite guidée : villa {n} chambres #shorts", "description": out["youtube"]["caption"]}
    return out


def main(start: str):
    d0 = date.fromisoformat(start)
    plans = {p["code"]: p for p in load_plans()}
    items = []
    for i in range(7):
        day = (d0 + timedelta(days=i)).isoformat()
        c = REELS[i]
        caps = captions(plans[c])
        assert not problems(plans[c], caps), (c, problems(plans[c], caps))
        items.append({"kind": "reel", "id": c, "video": f"reels/out/{c}.mp4", "scheduled_for": f"{day}T13:00:00", **caps})
        if i < len(TOURS):
            j = TOURS[i]
            caps = tour_caps(j)
            bad = [p for t in [caps["facebook"]["caption"], caps["youtube"]["title"]] for p in check_copy(t, [])]
            assert not bad, (j, bad)
            items.append({"kind": "tour", "id": j, "video": f"visite_plan/out/{j}.mp4", "scheduled_for": f"{day}T20:00:00", **caps})
    out = {"timezone": "Africa/Douala", "items": items}
    Path("week/SCHEDULE.json").write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for it in items:
        print(it["scheduled_for"], it["kind"], it["id"])


if __name__ == "__main__":
    main(sys.argv[1])
