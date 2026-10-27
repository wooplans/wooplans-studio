"""V2-2CH-01 : plan redessiné au style WooPlans, pièces recalées sur les murs, trajets par les portes."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from restyle import split_ink
from redraw import redraw, paths_json

src = Image.open(HERE / "source.png").convert("RGB")
a = np.asarray(src).astype(int)
ink = ((a[..., 2] - a[..., 0]) > 60) | (a.mean(-1) < 150)
LABELS = [(cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2) for cx, cy, w, h in
          [(310, 393, 180, 34), (564, 244, 60, 30), (759, 317, 150, 32), (967, 290, 125, 30), (1003, 600, 90, 30),
           (722, 680, 240, 32), (294, 825, 200, 32), (576, 925, 60, 30), (308, 1022, 160, 32), (845, 1051, 180, 66)]]
for x0, y0, x1, y1 in LABELS:
    ink[y0:y1, x0:x1] = False
raw, _ = split_ink(ink, 13)
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
ROOMS = [
    dict(name="Véranda", label="Véranda", poly=R(105, 910, 495, 1095), sol="ext", ouvert=True, stop=(325, 1010)),
    dict(name="Marches", poly=R(190, 1095, 450, 1215), sol="ext", ouvert=True),
    dict(name="Séjour", label="Séjour", poly=R(105, 470, 495, 910), label_xy=(294, 830), stop=(300, 700)),
    dict(name="Salle à manger", label="Salle à manger", poly=[(495, 465), (885, 465), (885, 705), (605, 705), (605, 800), (495, 800)],
         label_xy=(722, 680), stop=(560, 590)),
    dict(name="Cuisine", label="Cuisine", poly=R(630, 125, 885, 465), sol="cuisine", stop=(750, 395)),
    dict(name="Buanderie", label="Buanderie", poly=R(885, 125, 1050, 465), sol="eau", stop=(955, 390)),
    dict(name="Sortie de service", label="Sortie", poly=R(885, 465, 1050, 705), sol="ext", stop=(965, 650)),
    dict(name="Chambre 2", label="Chambre 2", poly=[(120, 125), (495, 125), (495, 355), (620, 355), (620, 465), (120, 465)],
         label_xy=(300, 393), stop=(300, 300)),
    dict(name="WC", label="WC", poly=R(495, 125, 620, 355), sol="eau", stop=(555, 240)),
    dict(name="Chambre parentale", label="Chambre\nparentale", poly=R(605, 705, 1050, 1090), label_xy=(845, 1045), stop=(720, 805)),
    dict(name="WC privé", label="WC", poly=R(495, 800, 605, 1065), sol="eau", label_xy=(552, 925)),
]
ORDER = ["Véranda", "Séjour", "Salle à manger", "Cuisine", "Sortie de service", "Buanderie", "Chambre 2", "WC", "Chambre parentale"]
CROP = (40, 50, 1160, 1310)
img, polys, walls = redraw(src, ink, raw, ROOMS, T=20, portes=[(495, 318, 56), (1050, 590, 70)])
img.crop(CROP).save(HERE / "plan.png")
paths_json(HERE, ROOMS, polys, walls, (320, 1170), ORDER, crop=CROP[:2])
