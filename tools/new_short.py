"""Crée un job de short « rendus 3D » : python tools/new_short.py <CODE> [n° de série] [--images a.png b.png ...]

Rendus d'origine (1920x1080 ou plus, sans filigrane du site) : par défaut tous ceux de shorts/rendus/<CODE>/, dans
l'ordre des noms ; le 1er doit être la plus belle façade (vue complète au début de la vidéo). 4 rendus au plus.
Écrit shorts/jobs/<CODE>-S<n>/short.json (sans musique : rotation dans la base Mixkit au rendu) ; vignette déduite
de data/plans.json. Pour lancer le rendu sur GitHub : créer shorts/jobs/<id>/RENDER et pousser.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
MAX_IMAGES = 4
EXT = {".png", ".jpg", ".jpeg", ".webp"}


def main(argv) -> int:
    images = []
    if "--images" in argv:
        i = argv.index("--images")
        argv, images = argv[:i], argv[i + 1:]
    code, serie = argv[0].upper(), int(argv[1]) if len(argv) > 1 else 1
    plans = json.loads((ROOT / "data" / "plans.json").read_text(encoding="utf-8"))
    p = next((p for p in plans if p["code"] == code), None)
    if not p:
        print("code absent de data/plans.json :", code)
        return 1
    if not images:
        src = ROOT / "shorts" / "rendus" / code
        images = [str(f.relative_to(ROOT)) for f in sorted(src.glob("*")) if f.suffix.lower() in EXT]
    if not images:
        print(f"aucun rendu : déposer les originaux dans shorts/rendus/{code}/ ou passer --images")
        return 1
    kind = "Duplex" if p["category"] == "duplex" else "Villa"
    chip = f"{p['surface']} m²" + (f" · terrain {p['land_area']} m²" if p.get("land_area") else "")
    job = ROOT / "shorts" / "jobs" / f"{code}-S{serie}"
    job.mkdir(parents=True, exist_ok=True)
    cfg = {"code": code, "images": images[:MAX_IMAGES],
           "thumbnail": {"title": f"{kind} {p['bedrooms']} chambres", "chip": chip}}
    (job / "short.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(job.relative_to(ROOT), "->", ", ".join(cfg["images"]))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
