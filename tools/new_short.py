"""Crée un job de short « rendus 3D » : python tools/new_short.py <CODE> [n° de série] [--images a.png b.png ...]

Rendus d'origine (1920x1080 ou plus, sans filigrane du site) :
- par défaut, pris DIRECTEMENT dans R2 par le site (wooplans/site_api.py, jeton WOOPLANS_MCP_TOKEN) : couverture en
  premier (vue complète au début de la vidéo), puis 3 autres répartis sur la galerie (jour, nuit, autres angles) ;
- sinon ceux de shorts/rendus/<CODE>/ (ordre des noms), ou la liste --images.
Téléchargés dans shorts/rendus/<CODE>/ (non commités) ; les clés R2 sont notées dans short.json pour un nouveau rendu.
Écrit shorts/jobs/<CODE>-S<n>/short.json (sans musique : rotation dans la base Mixkit au rendu).
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wooplans import site_api  # noqa: E402

MAX_IMAGES = 4
EXT = {".png", ".jpg", ".jpeg", ".webp"}


def spread(items: list, n: int = MAX_IMAGES) -> list:
    """Le 1er (couverture), puis n-1 éléments répartis régulièrement sur le reste de la galerie."""
    if len(items) <= n:
        return items
    rest = items[1:]
    step = len(rest) / (n - 1)
    return [items[0]] + [rest[min(len(rest) - 1, round(i * step + step / 2 - 0.5))] for i in range(n - 1)]


def r2_images(code: str):
    """Originaux R2 choisis et téléchargés : (chemins relatifs au dépôt, clés R2)."""
    chosen = spread(site_api.original_renders(code))
    paths, keys = [], []
    for k, r in enumerate(chosen, 1):
        ext = Path(r["key"]).suffix.lower() or ".png"
        dest = ROOT / "shorts" / "rendus" / code / f"{k:02d}{ext}"
        if not dest.exists():
            site_api.download(r["key"], dest)
        paths.append(str(dest.relative_to(ROOT)))
        keys.append(r["key"])
    return paths, keys


def ensure_images(cfg: dict) -> None:
    """Re-télécharge depuis R2 les images d'un job absentes du disque (nouveau rendu sur GitHub)."""
    for path, key in zip(cfg["images"], cfg.get("r2", [])):
        if not (ROOT / path).exists():
            site_api.download(key, ROOT / path)


def next_serie(code: str) -> int:
    n = 1
    while (ROOT / "shorts" / "jobs" / f"{code}-S{n}").exists():
        n += 1
    return n


def create(code: str, serie: int = 0, images=None) -> Path:
    code = code.upper()
    serie = serie or next_serie(code)
    keys = []
    if not images:
        local = ROOT / "shorts" / "rendus" / code
        images = [str(f.relative_to(ROOT)) for f in sorted(local.glob("*")) if f.suffix.lower() in EXT]
        if not images:
            images, keys = r2_images(code)
    if not images:
        raise SystemExit(f"{code} : aucun rendu d'origine exploitable (R2, shorts/rendus/{code}/ ou --images)")
    job = ROOT / "shorts" / "jobs" / f"{code}-S{serie}"
    job.mkdir(parents=True, exist_ok=True)
    cfg = {"code": code, "images": images[:MAX_IMAGES]}
    if keys:
        cfg["r2"] = keys[:MAX_IMAGES]
    (job / "short.json").write_text(json.dumps(cfg, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(job.relative_to(ROOT), "->", ", ".join(cfg["images"]))
    return job


def main(argv) -> int:
    images = []
    if "--images" in argv:
        i = argv.index("--images")
        argv, images = argv[:i], argv[i + 1:]
    create(argv[0], int(argv[1]) if len(argv) > 1 else 0, images)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
