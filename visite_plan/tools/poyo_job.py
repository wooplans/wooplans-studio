"""Plan Poyo (rendu réaliste sans texte) -> plan.png étiqueté + paths.json du job.

  python visite_plan/tools/poyo_job.py <job>

Reprend les pièces de redraw_job.py (coordonnées du plan source) et les reporte sur le rendu Poyo
(visite_plan/poyo/<job>.png) par correspondance des emprises des murs ; chaque pièce visitée est ensuite
remplie entre les murs du rendu Poyo (bornée par sa position reportée), le trajet du point passe par les portes.
"""
import json
import sys
import types
from pathlib import Path

import numpy as np
from PIL import Image

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
import redraw  # noqa: E402
from restyle import split_ink  # noqa: E402


def walls_bbox(walls, min_area=300):
    import cv2
    n, lab, st, _ = cv2.connectedComponentsWithStats(walls.astype(np.uint8), 8)
    keep = [i for i in range(1, n) if st[i, 4] >= min_area]
    xs0 = min(st[i, 0] for i in keep); ys0 = min(st[i, 1] for i in keep)
    xs1 = max(st[i, 0] + st[i, 2] for i in keep); ys1 = max(st[i, 1] + st[i, 3] for i in keep)
    return xs0, ys0, xs1, ys1


def main(job):
    here = TOOLS.parent / "jobs" / job
    cap = {}
    real = redraw.run_job
    redraw.run_job = lambda *a, **k: cap.update(args=a, kw=k)
    real_redraw, real_pj = redraw.redraw, redraw.paths_json
    ns = {"__file__": str(here / "redraw_job.py"), "__name__": "__poyo__"}
    if "run_job(" not in (here / "redraw_job.py").read_text(encoding="utf-8"):   # ancien format (V2) : on lit ses variables
        redraw.redraw = lambda *a, **k: (types.SimpleNamespace(crop=lambda c: types.SimpleNamespace(save=lambda p: None)), {}, None)
        redraw.paths_json = lambda *a, **k: None
    try:
        exec(compile((here / "redraw_job.py").read_text(encoding="utf-8"), str(here / "redraw_job.py"), "exec"), ns)
    finally:
        redraw.run_job, redraw.redraw, redraw.paths_json = real, real_redraw, real_pj
    if "args" in cap:
        _, src, ink, rooms, order, start, crop = cap["args"][:7]
        wall_px = cap["kw"].get("wall_px", 13)
    else:
        src, ink, rooms, order, start, crop = ns["src"], ns["ink"], ns["ROOMS"], ns["ORDER"], (320, 1170), ns["CROP"]
        wall_px = 13
        cap["kw"] = {"label_boxes": [((x0 + x1) // 2, (y0 + y1) // 2, x1 - x0, y1 - y0) for x0, y0, x1, y1 in ns["LABELS"]]}
    for cx, cy, w, h in cap["kw"].get("label_boxes", ()):
        ink[max(0, cy - h // 2):cy + h // 2, max(0, cx - w // 2):cx + w // 2] = False
    raw_src, _ = split_ink(ink, wall_px)
    poyo = Image.open(TOOLS.parent / "poyo" / f"{job}.png").convert("RGB")
    a = np.asarray(poyo).astype(int)
    pink = (a.mean(-1) < 75) & ((a.max(-1) - a.min(-1)) < 40)
    raw_p, _ = split_ink(pink, 12)
    s0, p0 = [int(v) for v in walls_bbox(raw_src)], [int(v) for v in walls_bbox(raw_p)]
    ax = (p0[2] - p0[0]) / (s0[2] - s0[0]); ay = (p0[3] - p0[1]) / (s0[3] - s0[1])
    T = lambda q: (int(round(p0[0] + (q[0] - s0[0]) * ax)), int(round(p0[1] + (q[1] - s0[1]) * ay)))
    old = {r["name"]: r for r in json.loads((here / "paths.json").read_text(encoding="utf-8"))["rooms"]}
    cx0, cy0 = crop[0], crop[1]
    new = []
    for r in rooms:
        n = dict(name=r["name"], label=r.get("label"), size=r.get("size", 24))
        if r["name"] in old:                       # pièce visitée : polygone du job (coordonnées plan.png + recadrage)
            poly = [T((x + cx0, y + cy0)) for x, y in old[r["name"]]["poly"]]
        else:
            poly = [T(q) for q in r["poly"]] if "poly" in r else None
        anchor = r.get("label_xy") or r.get("seed")
        if anchor is None and poly:
            xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
            anchor = None; n["label_xy"] = ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)
        else:
            n["label_xy"] = T(anchor)
        if poly:
            xs = [q[0] for q in poly]; ys = [q[1] for q in poly]
            m = 14
            n["box"] = (max(0, min(xs) - m), max(0, min(ys) - m), max(xs) + m, max(ys) + m)
            seed = T(r["seed"]) if "seed" in r else ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)
            n["seed"] = seed
            n["poly_fallback"] = poly
        else:
            n["poly"] = [n["label_xy"]] * 3
        if "stop" in r:
            n["stop"] = T(r["stop"])
        new.append(n)
    xs, ys = np.where(raw_p.any(0))[0], np.where(raw_p.any(1))[0]
    pc = (max(0, p0[0] - 40), max(0, p0[1] - 40), min(poyo.width, p0[2] + 40), min(poyo.height, p0[3] + 40))
    for n in new:                                  # le départ et les arrêts restent dans le recadrage
        if "stop" in n:
            n["stop"] = (min(max(n["stop"][0], pc[0] + 5), pc[2] - 5), min(max(n["stop"][1], pc[1] + 5), pc[3] - 5))
    st = T(start)
    st = (min(max(st[0], pc[0] + 8), pc[2] - 8), min(max(st[1], pc[1] + 8), pc[3] - 8))
    real(here, poyo, pink, new, order, st, pc, wall_px=12, keep_src=True, close_px=20, fp_close=120)


if __name__ == "__main__":
    main(sys.argv[1])
