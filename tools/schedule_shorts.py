"""Calendrier de publication des shorts « rendus 3D » : écrit shorts/jobs/<id>/PUBLISH.json pour chaque job, dans l'ordre.

  python tools/schedule_shorts.py --start 2026-10-29 --times 12:15,17:45,20:30 D4-001-S1 D4-011-S1 ...

N créneaux par jour (un par heure de --times, fuseau Africa/Douala) à partir de --start. Textes : modèle, chambres,
surface, terrain (data/plans.json, sinon la fiche du site relevée dans shorts/INVENTAIRE.json), lien du catalogue avec
UTM par plateforme. JAMAIS de prix (décision de Tao du 28 oct.) : chaque texte passe par check_copy.
Pousser les PUBLISH.json (SEULEMENT après l'accord de Tao) -> workflow publish-zernio (Facebook + YouTube) ;
TikTok @wooplans : WoopSocial (légende « tiktok_woopsocial », publiée par Claude avec le connecteur).
"""
import argparse
import json
import sys
from datetime import date, timedelta
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wooplans import shorts  # noqa: E402
from wooplans.guardrails import check_copy  # noqa: E402
from wooplans.utm import build_link  # noqa: E402

TZ = "Africa/Douala"
TAGS = "#plandemaison #{cat} #maison #construction #architecture #Cameroun #Afrique"


def facts(code: str) -> dict:
    """Chiffres du modèle : data/plans.json (PDF) en priorité, sinon la fiche du site (inventaire)."""
    p = next((p for p in shorts.local_plans() if p["code"] == code), None)
    if p is None:
        inv = ROOT / "shorts" / "INVENTAIRE.json"
        p = next(m for m in json.loads(inv.read_text(encoding="utf-8")) if m["code"] == code)
    return p


def captions(job: str) -> dict:
    code = json.loads((shorts.JOBS / job / "short.json").read_text(encoding="utf-8"))["code"]
    p = facts(code)
    kind = "Duplex" if p["category"] == "duplex" else "Villa"
    first = f"{kind} {p['bedrooms']} chambres de {p['surface']} m²" + (
        f", pour un terrain de {p['land_area']} m²" if p.get("land_area") else "") + " 🏡"

    def body(plat: str) -> str:
        return (f"{first}\nModèle {code} : plans cotés et devis détaillé disponibles.\n\n"
                f"Découvrez le Catalogue Premium 👉 {build_link(plat, 'S', job)}\n\n" + TAGS.format(cat=p["category"]))

    out = {"facebook": {"caption": body("facebook")},
           "youtube": {"title": f"{kind} {p['bedrooms']} chambres, {p['surface']} m² : modèle {code} #shorts",
                       "description": body("youtube")},
           "tiktok_woopsocial": {"caption": body("tiktok")}}
    texts = [out["facebook"]["caption"], out["youtube"]["title"], out["youtube"]["description"],
             out["tiktok_woopsocial"]["caption"]]
    problems = [x for t in texts for x in check_copy(t)]
    if problems:
        raise SystemExit(f"{job} : texte refusé {problems}")
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", required=True, help="premier jour, AAAA-MM-JJ")
    ap.add_argument("--times", default="12:15,17:45,20:30", help="heures de publication (Douala), séparées par des virgules")
    ap.add_argument("jobs", nargs="+")
    a = ap.parse_args()
    times, day0 = a.times.split(","), date.fromisoformat(a.start)
    for i, job in enumerate(a.jobs):
        when = f"{day0 + timedelta(days=i // len(times))}T{times[i % len(times)]}:00"
        cfg = {"video": f"shorts/out/{job}.mp4", "scheduled_for": when, "timezone": TZ, **captions(job)}
        (shorts.JOBS / job / "PUBLISH.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(when, job)
    return 0


if __name__ == "__main__":
    sys.exit(main())
