"""Prépare un lot de shorts pour le workflow short-render : python tools/shorts_batch.py "<sélection>" [--jobs id ...]

Sélection : codes, catégorie, type, « tous », « nouveaux » (voir wooplans/shorts.py). Chaque modèle reçoit un
nouveau job <CODE>-S<n> (images prises dans R2 au moment du rendu) ; --jobs relance des jobs existants.
Musique attribuée ici pour tout le lot (rotation : jamais deux fois la même dans un lot).
Sortie (stdout) : une ligne JSON [{"job", "code", "music", "new"}, ...].
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wooplans import music, shorts  # noqa: E402

MAX_BATCH = 40                     # garde-fou : au-delà, découper la demande


def plan(selection: str = "", jobs=()) -> list:
    used, rows, series = music.usage(), [], {}
    for job in jobs:
        cfg = json.loads((shorts.JOBS / job / "short.json").read_text(encoding="utf-8"))
        rows.append({"job": job, "code": cfg["code"], "music": cfg.get("music") or "", "new": False})
    for code in (shorts.resolve(selection) if selection.strip() else []):
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
