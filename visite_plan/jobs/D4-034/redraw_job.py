"""D4-034 (duplex) : plans RDC + étage redessinés au style WooPlans à partir des captures du PDF (source_rdc.png, source_etage.png),
pièces recalées sur les murs, trajets par les portes. Produit plan.png (RDC), plan_etage.png, paths.json, paths_check.png.
Relancer après toute retouche : python visite_plan/jobs/D4-034/redraw_job.py"""
import json
import sys
import tempfile
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import redraw, paths_json
from restyle import split_ink

CANVAS = (1640, 1800)
CROP = (150, 20, 1640, 1700)              # même cadre pour les deux niveaux
SHIFT = (141, -140)                        # l'étage est calé sur le RDC (même coin haut-gauche de la maison)
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]


def level(file, shift, text, steps):
    base = Image.open(HERE / file).convert("RGB")
    src = Image.new("RGB", CANVAS, (255, 255, 255)); src.paste(base, shift)
    a = np.asarray(src).astype(int)
    dark = (a.mean(-1) < 110) & ((a.max(-1) - a.min(-1)) < 40)               # murs et textes noirs
    green = (a[..., 1] - a[..., 0] > 60) & (a[..., 1] - a[..., 2] > 60)       # mobilier vert
    for x0, y0, x1, y1 in text:
        dark[y0 + shift[1]:y1 + shift[1], x0 + shift[0]:x1 + shift[0]] = False
    raw, _ = split_ink(dark, 13)
    return src, dark | green, raw


def add_steps(img, boxes):
    d = ImageDraw.Draw(img)
    for x0, y0, x1, y1, n in boxes:
        d.rectangle((x0, y0, x1, y1), outline=(150, 150, 150), width=2)
        for i in range(1, n):
            x = x0 + (x1 - x0) * i // n
            d.line([(x, y0), (x, y1)], fill=(170, 170, 170), width=2)


def shifted(rooms):
    out = []
    for r in rooms:
        r = dict(r)
        for k in ("poly",):
            r[k] = [(x + SHIFT[0], y + SHIFT[1]) for x, y in r[k]]
        for k in ("label_xy", "stop"):
            if k in r:
                r[k] = (r[k][0] + SHIFT[0], r[k][1] + SHIFT[1])
        out.append(r)
    return out


def check(img, paths, out, cols=((240, 138, 46), (200, 0, 0), (0, 160, 0), (160, 0, 200), (0, 160, 160), (200, 120, 0))):
    im = img.crop(CROP).convert("RGB"); d = ImageDraw.Draw(im, "RGBA")
    for i, r in enumerate(paths):
        c = cols[i % len(cols)]
        d.polygon([tuple(p) for p in r["poly"]], fill=c + (40,), outline=c + (255,))
        d.line([tuple(p) for p in r["path"]], fill=c + (255,), width=5)
    im.save(out)


# ============================ RDC ============================
TEXT0 = [(155, 245, 380, 340), (615, 235, 805, 325), (1180, 215, 1370, 310), (1155, 895, 1365, 985), (800, 1000, 985, 1085),
         (415, 1210, 665, 1300), (300, 890, 495, 990), (1020, 1470, 1245, 1555), (30, 750, 130, 860), (860, 1690, 940, 1780),
         (200, 420, 260, 460)]
src0, ink0, raw0 = level("source_rdc.png", (0, 0), TEXT0, None)
ROOMS0 = [
    dict(name="Terrasse 1", label="Terrasse 1", poly=R(777, 1385, 1590, 1575), sol="ext", ouvert=True, label_xy=(1180, 1490), stop=(1000, 1480)),
    dict(name="Salon", label="Salon", poly=R(1010, 470, 1578, 1385), label_xy=(1290, 960), stop=(1290, 1200)),
    dict(name="Entrée", label="Entrée", poly=R(777, 470, 1010, 1385), label_xy=(893, 1010), stop=(893, 1180)),
    dict(name="Salle à manger", label="Salle à manger", poly=R(1010, 55, 1578, 470), label_xy=(1290, 260), size=22, stop=(1290, 400)),
    dict(name="Cuisine", label="Cuisine", poly=R(402, 55, 1010, 470), sol="cuisine", label_xy=(700, 280), stop=(700, 300)),
    dict(name="Terrasse 2", label="Terrasse 2", poly=R(218, 45, 402, 460), sol="ext", ouvert=True, label_xy=(310, 260), size=20),
    dict(name="Escalier", poly=[(218, 470), (777, 470), (777, 1030), (612, 1030), (612, 822), (218, 822)], stop=(660, 650)),
    dict(name="SDB", label="SDB", poly=R(218, 822, 612, 1030), sol="eau", label_xy=(410, 930), size=22, stop=(410, 940)),
    dict(name="Chambre V.", label="Chambre V.", poly=[(218, 1030), (777, 1030), (777, 1566), (648, 1566), (648, 1480), (351, 1480), (351, 1566), (218, 1566)],
         label_xy=(500, 1270), stop=(520, 1250)),
]
PORTES0 = [(893, 1385, 170), (1290, 1385, 220), (1010, 975, 300), (777, 640, 300), (930, 470, 130), (402, 395, 130),
           (777, 1135, 100), (612, 925, 100), (1290, 470, 480)]
ORDER0 = ["Terrasse 1", "Salon", "Entrée", "Salle à manger", "Cuisine", "Chambre V.", "Escalier"]
img0, polys0, walls0 = redraw(src0, ink0, raw0, ROOMS0, T=22, auto_gaps=False, portes=PORTES0)
add_steps(img0, [(400, 490, 770, 640, 10), (400, 655, 770, 805, 9)])
img0.crop(CROP).save(HERE / "plan.png")

# ============================ ÉTAGE ============================
TEXT1 = [(285, 375, 525, 465), (795, 350, 975, 440), (1080, 470, 1320, 560), (715, 700, 900, 795), (215, 1000, 400, 1095),
         (1015, 1130, 1240, 1220), (285, 1350, 470, 1435), (910, 1545, 1135, 1630), (500, 1740, 890, 1800), (0, 0, 430, 25)]
src1, ink1, raw1 = level("source_etage.png", SHIFT, TEXT1, None)
ROOMS1 = [
    dict(name="Hall", label="Hall", poly=R(617, 585, 970, 922), label_xy=(795, 750), stop=(795, 750)),
    dict(name="Chambre 3", label="Chambre 3", poly=R(77, 185, 770, 585), label_xy=(400, 400), stop=(400, 420)),
    dict(name="SDB 2", label="SDB 2", poly=R(770, 185, 970, 585), sol="eau", label_xy=(870, 390), size=22, stop=(870, 420)),
    dict(name="Chambre 2", label="Chambre 2", poly=R(970, 185, 1385, 922), label_xy=(1180, 500), stop=(1180, 700)),
    dict(name="Chambre 1", label="Chambre 1", poly=R(617, 922, 1385, 1460), label_xy=(1120, 1170), stop=(1000, 1250)),
    dict(name="SDB 1", label="SDB 1", poly=R(77, 922, 617, 1190), sol="eau", label_xy=(300, 1040), size=22, stop=(340, 1130)),
    dict(name="Dressing", label="Dressing", poly=[(77, 1190), (617, 1190), (617, 1650), (490, 1650), (490, 1565), (205, 1565), (205, 1650), (77, 1650)],
         sol="eau", label_xy=(375, 1380), stop=(375, 1380)),
    dict(name="Terrasse étage", label="Terrasse étage", poly=R(617, 1460, 1385, 1690), sol="ext", ouvert=True, label_xy=(1010, 1580), size=22, stop=(1000, 1580)),
    dict(name="Escalier étage", poly=R(77, 585, 617, 922)),
]
PORTES1 = [(695, 585, 120), (835, 585, 100), (970, 850, 140), (688, 922, 140), (617, 1135, 100), (617, 1370, 180),
           (1000, 1460, 400), (617, 750, 325)]
ORDER1 = ["Hall", "Chambre 3", "Chambre 2", "Chambre 1", "Terrasse étage"]
ROOMS1s = shifted(ROOMS1)
PORTES1s = [(x + SHIFT[0], y + SHIFT[1], w) for x, y, w in PORTES1]
img1, polys1, walls1 = redraw(src1, ink1, raw1, ROOMS1s, T=22, auto_gaps=False, portes=PORTES1s)
add_steps(img1, [(165 + SHIFT[0], 595 + SHIFT[1], 610 + SHIFT[0], 745 + SHIFT[1], 10),
                 (165 + SHIFT[0], 755 + SHIFT[1], 610 + SHIFT[0], 905 + SHIFT[1], 9)])
img1.crop(CROP).save(HERE / "plan_etage.png")

# ============================ trajets ============================
START0 = (1000, 1560)
JUMP = (795 + SHIFT[0], 750 + SHIFT[1])          # on arrive à l'étage au niveau du hall
with tempfile.TemporaryDirectory() as t0, tempfile.TemporaryDirectory() as t1:
    r0 = paths_json(t0, ROOMS0, polys0, walls0, START0, ORDER0, crop=CROP[:2])
    r1 = paths_json(t1, ROOMS1s, polys1, walls1, JUMP, ORDER1, crop=CROP[:2])
tr = lambda q: [round(q[0] - CROP[0], 1), round(q[1] - CROP[1], 1)]
for r in r0:
    if r["name"] == "Escalier":
        r["switch_to"] = 1
        r["jump_to"] = tr(JUMP)
out = {"start": tr(START0), "rooms": r0 + r1}
(HERE / "paths.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
meta = json.loads((HERE / "meta.json").read_text(encoding="utf-8"))
meta["plan_px"] = [CROP[2] - CROP[0], CROP[3] - CROP[1]]
(HERE / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=1), encoding="utf-8")
check(img0, r0, HERE / "paths_check.png")
check(img1, r1, HERE / "paths_check_etage.png")
print("ok", meta["plan_px"])
