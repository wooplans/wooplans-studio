"""Prépare un lot de shorts pour le workflow short-render : python tools/shorts_batch.py "<sélection>" [--jobs id ...]

Sélection : codes, catégorie, type, « tous », « nouveaux » (voir wooplans/shorts.py). Chaque modèle reçoit un
nouveau job <CODE>-S<n> (images prises dans R2 au moment du rendu) ; --jobs relance des jobs existants.
Modèles sans 3 rendus exploitables dans R2 : écartés (raison sur stderr). Mot « inventaire » : écrit
shorts/INVENTAIRE.md (état de tout le catalogue).
Musique attribuée ici pour tout le lot (rotation : jamais deux fois la même dans un lot).
Sortie (stdout) : une ligne JSON [{"job", "code", "music", "new"}, ...].
"""
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.new_short import MIN_IMAGES  # noqa: E402
from wooplans import music, shorts, site_api  # noqa: E402

MAX_BATCH = 40                     # garde-fou : au-delà, découper la demande
REPORT = ROOT / "shorts" / "INVENTAIRE.md"


def ineligible(code: str) -> str:
    """Raison d'écarter un modèle (moins de MIN_IMAGES rendus exploitables dans R2), vide s'il est prêt."""
    if not os.environ.get("WOOPLANS_MCP_TOKEN"):
        return ""                                          # hors GitHub : vérifié au téléchargement
    try:
        n = len(site_api.usable_renders(code))
    except Exception as e:
        return f"inventaire R2 illisible ({e})"
    return "" if n >= MIN_IMAGES else f"{n} rendu(s) exploitable(s) dans R2 (originaux absents), {MIN_IMAGES} au moins"


def inventory() -> None:
    """shorts/INVENTAIRE.md : pour chaque modèle publié, originaux R2, anciennes images propres utilisables, état."""
    lines = ["# Inventaire des rendus pour les shorts", "",
             "Prêt = au moins 3 rendus exploitables (original R2 propre, ou ancienne image du site sans filigrane "
             f"d'au moins {site_api.MIN_SITE_WIDTH} px). Mis à jour par le workflow short-render (mot « inventaire »).", "",
             "| Modèle | Rendus en ligne | Originaux R2 | Anciennes images utilisables | Prêt | Shorts déjà faits |",
             "|---|---|---|---|---|---|"]
    ready = 0
    for p in shorts.catalogue():
        code = p["code"]
        try:
            idx = site_api.plan_files(code)
        except Exception as e:
            lines.append(f"| {code} | ? | ? | ? | erreur : {e} | |")
            continue
        usable = site_api.usable_renders(code, idx)
        orig = sum(u["source"] == "original" for u in usable)
        ok = len(usable) >= MIN_IMAGES
        ready += ok
        done = len(list(shorts.JOBS.glob(f"{code}-S*/short.json")))
        lines.append(f"| {code} | {idx['summary']['renders']} | {orig} | {len(usable) - orig} | {'oui' if ok else 'non'} | {done} |")
    lines.insert(3, f"**{ready} modèle(s) prêt(s).**")
    lines.insert(4, "")
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"inventaire : {ready} modèle(s) prêt(s) -> {REPORT.relative_to(ROOT)}", file=sys.stderr)


def plan(selection: str = "", jobs=()) -> list:
    used, rows, series = music.usage(), [], {}
    for job in jobs:
        cfg = json.loads((shorts.JOBS / job / "short.json").read_text(encoding="utf-8"))
        rows.append({"job": job, "code": cfg["code"], "music": cfg.get("music") or "", "new": False})
    words = selection.split()
    if any(w.lower() == "inventaire" for w in words):
        inventory()
        words = [w for w in words if w.lower() != "inventaire"]
    for code in (shorts.resolve(" ".join(words)) if words else []):
        why = ineligible(code)
        if why:
            print(f"ignoré {code} : {why}", file=sys.stderr)
            continue
        n = series.get(code) or 1
        while (shorts.JOBS / f"{code}-S{n}").exists():
            n += 1
        series[code] = n + 1
        rows.append({"job": f"{code}-S{n}", "code": code, "music": "", "new": True})
    if len(rows) > MAX_BATCH:
        raise SystemExit(f"{len(rows)} shorts demandés : {MAX_BATCH} au plus par lot, découper la sélection")
    for r in rows:
        if not r["music"]:
            r["music"] = music.pick(r["job"], used)
        used[r["music"]] += 1
    return rows


if __name__ == "__main__":
    args = sys.argv[1:]
    jobs = []
    if "--jobs" in args:
        i = args.index("--jobs")
        args, jobs = args[:i], args[i + 1:]
    print(json.dumps(plan(" ".join(args), jobs)))
