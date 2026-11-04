"""D4-034 (duplex) : plans améliorés Poyo (poyo_rdc.png, poyo_etage.png, sans texte) -> plan.png, plan_etage.png (étiquettes WooPlans),
paths.json (trajets par les portes, escalier avec switch_to/jump_to), paths_check*.png.
Coordonnées des pièces = pixels des images Poyo. Relancer après toute retouche."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from restyle import label as draw_label, shortest_path, split_ink

O = 120                                              # marge blanche autour des images (cadres décalés)
CROPS = {0: (60, 40, 960, 1010), 1: (20, 75, 920, 1045)}   # même cadre 900 x 970, étage calé sur le RDC
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]

LEVELS = {
    0: dict(file="poyo_rdc.png", out="plan.png", start=(700, 915), order=["Terrasse 1", "Salon", "Entrée", "Salle à manger", "Cuisine", "Chambre V.", "Escalier"],
            rooms=[
                dict(name="Terrasse 1", label="Terrasse 1", poly=R(452, 815, 905, 905), label_xy=(680, 862), stop=(640, 870)),
                dict(name="Salon", label="Salon", poly=R(580, 305, 895, 810), label_xy=(745, 560), stop=(740, 700)),
                dict(name="Entrée", label="Entrée", poly=R(452, 305, 575, 815), label_xy=(513, 560), size=20, stop=(513, 720)),
                dict(name="Salle à manger", label="Salle à manger", poly=R(580, 75, 895, 298), label_xy=(738, 262), size=20, stop=(738, 262)),
                dict(name="Cuisine", label="Cuisine", poly=R(240, 75, 570, 298), label_xy=(410, 215), size=22, stop=(410, 235)),
                dict(name="Terrasse 2", label="Terrasse 2", poly=R(125, 62, 225, 290), label_xy=(172, 200), size=16),
                dict(name="Escalier", poly=[(135, 307), (450, 307), (450, 605), (352, 605), (352, 497), (135, 497)], stop=(330, 420)),
                dict(name="SDB", label="SDB", poly=R(135, 505, 350, 598), label_xy=(260, 575), size=18),
                dict(name="Chambre V.", label="Chambre V.", poly=[(135, 610), (442, 610), (442, 915), (365, 915), (365, 865), (205, 865), (205, 915), (135, 915)],
                     label_xy=(300, 650), size=20, stop=(350, 760)),
            ]),
    1: dict(file="poyo_etage.png", out="plan_etage.png", start=(500, 420), order=["Hall", "Chambre 3", "Chambre 2", "Chambre 1", "Terrasse étage"],
            rooms=[
                dict(name="Hall", label="Hall", poly=R(405, 325, 600, 505), label_xy=(502, 440), size=22, stop=(500, 420)),
                dict(name="Chambre 3", label="Chambre 3", poly=R(80, 100, 480, 320), label_xy=(135, 285), size=18, stop=(300, 310)),
                dict(name="SDB 2", label="SDB 2", poly=R(495, 100, 600, 320), label_xy=(548, 215), size=14, stop=(548, 260)),
                dict(name="Chambre 2", label="Chambre 2", poly=R(610, 100, 845, 505), label_xy=(715, 450), size=18, stop=(715, 430)),
                dict(name="Chambre 1", label="Chambre 1", poly=R(405, 515, 845, 810), label_xy=(770, 770), size=22, stop=(500, 620)),
                dict(name="SDB 1", label="SDB 1", poly=R(90, 520, 400, 655), label_xy=(310, 612), size=16, stop=(300, 590)),
                dict(name="Dressing", label="Dressing", poly=[(95, 670), (398, 670), (398, 930), (318, 930), (318, 880), (165, 880), (165, 930), (95, 930)],
                     label_xy=(250, 790), size=20, stop=(250, 780)),
                dict(name="Terrasse étage", label="Terrasse étage", poly=R(405, 815, 845, 945), label_xy=(625, 880), size=20, stop=(625, 880)),
                dict(name="Escalier étage", poly=R(90, 325, 405, 505)),
            ]),
}
CLOSURES = {0: [], 1: []}
OPENINGS = {0: [], 1: []}
COLS = [(240, 138, 46), (200, 0, 0), (0, 160, 0), (160, 0, 200), (0, 160, 160), (200, 120, 0), (255, 0, 120), (90, 90, 90)]


def run():
    allrooms, plans = [], {}
    for lv, spec in LEVELS.items():
        base = Image.open(HERE / spec["file"]).convert("RGB")
        img = Image.new("RGB", (base.width + 2 * O, base.height + 2 * O), (255, 255, 255)); img.paste(base, (O, O))
        a = np.asarray(img).astype(int)
        ink = (a.mean(-1) < 80) & ((a.max(-1) - a.min(-1)) < 40)
        walls, _ = split_ink(ink, 14)
        for x0, y0, x1, y1 in CLOSURES[lv]:
            walls[y0 + O:y1 + O, x0 + O:x1 + O] = True
        for x0, y0, x1, y1 in OPENINGS[lv]:
            walls[y0 + O:y1 + O, x0 + O:x1 + O] = False
        off = lambda p: [(x + O, y + O) for x, y in p]
        polys = {r["name"]: off(r["poly"]) for r in spec["rooms"]}
        fp = np.zeros(walls.shape, np.uint8)
        for p in polys.values():
            cv2.fillPoly(fp, [np.array(p, np.int32)], 1)
        fp = cv2.dilate(fp, np.ones((41, 41), np.uint8))
        d = ImageDraw.Draw(img)
        for r in spec["rooms"]:
            if r.get("label"):
                draw_label(d, (r["label_xy"][0] + O, r["label_xy"][1] + O), r["label"], r.get("size", 22))
        cx0, cy0, cx1, cy1 = [v + O for v in CROPS[lv]]
        img.crop((cx0, cy0, cx1, cy1)).save(HERE / spec["out"])
        tr = lambda q, cx0=cx0, cy0=cy0: [round(q[0] - cx0, 1), round(q[1] - cy0, 1)]
        pos, out = (spec["start"][0] + O, spec["start"][1] + O), []
        for name in spec["order"]:
            by = next(r for r in spec["rooms"] if r["name"] == name)
            stop = (by["stop"][0] + O, by["stop"][1] + O)
            try:
                path = shortest_path(walls, pos, stop, 8, footprint=fp)
            except ValueError as e:
                print("ATTENTION", lv, name, e); path = [list(pos), list(stop)]
            out.append({"name": name, "path": [tr(q) for q in path], "poly": [tr(q) for q in polys[name]]})
            pos = stop
        plans[lv] = (out, tr, spec)
        im = Image.open(HERE / spec["out"]).convert("RGB"); dd = ImageDraw.Draw(im, "RGBA")
        for i, r in enumerate(out):
            c = COLS[i % len(COLS)]
            dd.polygon([tuple(p) for p in r["poly"]], fill=c + (45,), outline=c + (255,))
            dd.line([tuple(p) for p in r["path"]], fill=c + (255,), width=5)
        im.save(HERE / ("paths_check.png" if lv == 0 else "paths_check_etage.png"))
    out0, tr0, spec0 = plans[0]
    out1, tr1, spec1 = plans[1]
    jump = tr1((LEVELS[1]["start"][0] + O, LEVELS[1]["start"][1] + O))
    for r in out0:
        if r["name"] == "Escalier":
            r["switch_to"] = 1; r["jump_to"] = jump
    (HERE / "paths.json").write_text(json.dumps({"start": tr0((LEVELS[0]["start"][0] + O, LEVELS[0]["start"][1] + O)),
                                                  "rooms": out0 + out1}, ensure_ascii=False, indent=1), encoding="utf-8")
    meta = json.loads((HERE / "meta.json").read_text(encoding="utf-8"))
    w, h = CROPS[0][2] - CROPS[0][0], CROPS[0][3] - CROPS[0][1]
    meta["plan_px"] = [w, h]
    (HERE / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
    print("ok", w, h)


if __name__ == "__main__":
    run()
