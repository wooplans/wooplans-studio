"""Plan Poyo (sans texte) + pièces relevées sur le rendu -> plan.png étiqueté, paths.json, paths_check.png.

  python visite_plan/tools/poyo_rooms.py <job>

Lit jobs/<job>/poyo_rooms.json : {"crop": [x0, y0, x1, y1], "start": [x, y], "order": [...],
  "rooms": [{"name", "label", "poly": [[x, y], ...] ou "rect": [x0, y0, x1, y1], "stop": [x, y], "label_xy", "size"}]}
(coordonnées du rendu Poyo visite_plan/poyo/<job>.png). Les murs sont repris du rendu (gris foncé) ; le trajet du point
est le plus court chemin hors des murs, donc par les portes.
"""
import json
import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw

TOOLS = Path(__file__).resolve().parent
sys.path.insert(0, str(TOOLS))
from restyle import label as draw_label, shortest_path, split_ink  # noqa: E402

COLS = [(240, 138, 46), (200, 0, 0), (0, 160, 0), (160, 0, 200), (0, 160, 160), (200, 120, 0), (255, 0, 120),
        (90, 90, 90), (0, 0, 0), (0, 120, 255), (120, 60, 0), (0, 90, 60)]


def main(job, clear_px=8):
    here = TOOLS.parent / "jobs" / job
    spec = json.loads((here / "poyo_rooms.json").read_text(encoding="utf-8"))
    img = Image.open(TOOLS.parent / "poyo" / f"{job}.png").convert("RGB")
    a = np.asarray(img).astype(int)
    ink = (a.mean(-1) < 80) & ((a.max(-1) - a.min(-1)) < 40)
    walls, _ = split_ink(ink, spec.get("wall_px", 14))
    for x0, y0, x1, y1 in spec.get("closures", []):
        walls[y0:y1, x0:x1] = True
    for x0, y0, x1, y1 in spec.get("openings", []):
        walls[y0:y1, x0:x1] = False
    polys = {}
    fp = np.zeros(walls.shape, np.uint8)
    for r in spec["rooms"]:
        p = r.get("poly") or [[r["rect"][0], r["rect"][1]], [r["rect"][2], r["rect"][1]],
                              [r["rect"][2], r["rect"][3]], [r["rect"][0], r["rect"][3]]]
        polys[r["name"]] = p
        cv2.fillPoly(fp, [np.array(p, np.int32)], 1)
    for p in spec.get("free", []):              # zones de passage hors pièces (marches, couloir)
        cv2.fillPoly(fp, [np.array(p, np.int32)], 1)
    fp = cv2.dilate(fp, np.ones((71, 71), np.uint8))   # couvre les épaisseurs de murs entre deux pièces
    d = ImageDraw.Draw(img)
    for r in spec["rooms"]:
        if r.get("label"):
            p = polys[r["name"]]; xs = [q[0] for q in p]; ys = [q[1] for q in p]
            draw_label(d, tuple(r.get("label_xy") or ((min(xs) + max(xs)) // 2, (min(ys) + max(ys)) // 2)),
                       r["label"], r.get("size", 24))
    x0, y0, x1, y1 = spec["crop"]
    img.crop((x0, y0, x1, y1)).save(here / "plan.png")
    by = {r["name"]: r for r in spec["rooms"]}
    pos, out = tuple(spec["start"]), []
    tr = lambda q: [round(q[0] - x0, 1), round(q[1] - y0, 1)]
    for name in spec["order"]:
        stop = tuple(by[name]["stop"])
        try:
            path = shortest_path(walls, pos, stop, clear_px, footprint=fp)
        except ValueError as e:
            print("ATTENTION", name, e); path = [list(pos), list(stop)]
        out.append({"name": name, "path": [tr(q) for q in path], "poly": [tr(q) for q in polys[name]]})
        pos = stop
    (here / "paths.json").write_text(json.dumps({"start": tr(spec["start"]), "rooms": out}, ensure_ascii=False, indent=1),
                                     encoding="utf-8")
    meta = json.loads((here / "meta.json").read_text(encoding="utf-8"))
    meta["plan_px"] = [x1 - x0, y1 - y0]
    (here / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    im = Image.open(here / "plan.png").convert("RGB"); dd = ImageDraw.Draw(im, "RGBA")
    for i, r in enumerate(out):
        c = COLS[i % len(COLS)]
        dd.polygon([tuple(p) for p in r["poly"]], fill=c + (45,), outline=c + (255,))
        dd.line([tuple(p) for p in r["path"]], fill=c + (255,), width=5)
    im.save(here / "paths_check.png")


if __name__ == "__main__":
    main(sys.argv[1])
