"""V3-3CH-03 : plan bleu (type « blueprint ») redessiné au style WooPlans (murs, portes, pièces relevés sur l'image),
mobilier repris en gris, étiquettes WooPlans, trajets par les portes."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import run_job
from relabel import erase_text

S = Image.open(HERE / "source.png").convert("RGB")
OLD = [(292, 232, 62, 13), (497, 121, 38, 23), (700, 232, 62, 13), (262, 404, 66, 12), (438, 420, 30, 13), (712, 431, 50, 13),
       (372, 641, 50, 13), (633, 778, 86, 13), (812, 693, 50, 13), (783, 884, 68, 12), (596, 1054, 54, 13), (310, 1077, 56, 26),
       (449, 1087, 18, 12)]
for x, y, hw, hh in OLD:
    S = erase_text(S, x, y, hw, hh, dark=150, maxh=2 * hh + 6, grow=5)
a = np.asarray(S).astype(float)
ink = ((a[..., 2] - a[..., 0]) > 70) & (a.mean(-1) < 200)
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
ROOMS = [
    dict(name="Porche d'entrée", label="Porche\nd'entrée", poly=R(195, 925, 405, 1175), label_xy=(310, 1077), size=22, stop=(330, 1040)),
    dict(name="Séjour", label="Séjour", poly=[(125, 470), (500, 470), (500, 810), (415, 810), (415, 915), (125, 915)], label_xy=(372, 641), stop=(300, 700)),
    dict(name="Salle à manger", label="Salle à manger", poly=R(500, 600, 750, 805), label_xy=(633, 778), size=22, stop=(600, 700)),
    dict(name="Cuisine", label="Cuisine", poly=R(560, 340, 855, 600), sol="cuisine", label_xy=(712, 431), stop=(700, 480)),
    dict(name="Terrasse", label="Terrasse", poly=R(755, 600, 860, 805), ouvert=True, sol="ext", label_xy=(812, 693), size=20, stop=(808, 700)),
    dict(name="Chambre 1", label="Chambre 1", poly=R(125, 40, 430, 335), label_xy=(292, 232), stop=(290, 200)),
    dict(name="SDB 1", label="Salle de bain", poly=R(135, 340, 340, 470), sol="eau", label_xy=(262, 404), size=16, stop=(250, 410)),
    dict(name="Chambre 2", label="Chambre 2", poly=[(555, 40), (860, 40), (860, 335), (495, 335), (495, 205), (555, 205)], label_xy=(700, 232), stop=(700, 200)),
    dict(name="SDB 2", label="Salle\nde bain", poly=R(440, 45, 555, 205), sol="eau", label_xy=(497, 120), size=17, stop=(495, 140)),
    dict(name="Chambre parentale", label="Chambre\nparentale", poly=[(505, 815), (665, 815), (665, 910), (805, 910), (805, 1205), (505, 1205)], label_xy=(596, 1054), stop=(600, 1000)),
    dict(name="WC parental", label="WC / SDB", poly=R(665, 815, 865, 910), sol="eau", label_xy=(783, 862), size=15),
    dict(name="WC", label="WC", poly=R(420, 1010, 505, 1145), sol="eau", label_xy=(463, 1100), size=16),
    dict(name="Hall", label="Hall", poly=R(340, 335, 500, 470), label_xy=(420, 420), stop=(420, 400)),
    dict(name="Cellier", poly=R(505, 470, 640, 600), sol="cuisine"),
    dict(name="Dégagement", poly=R(415, 810, 505, 1010)),
    dict(name="Placard", poly=R(435, 205, 495, 335)),
]
ORDER = ["Porche d'entrée", "Séjour", "Salle à manger", "Cuisine", "Terrasse", "Hall", "SDB 1", "Chambre 1", "Chambre 2", "SDB 2", "Chambre parentale"]
meta = HERE / "meta.json"
if not meta.exists():
    meta.write_text(json.dumps({"band": "Villa  ·  3 chambres", "facade": False, "plan_px": [0, 0], "bottom_px": 440}, ensure_ascii=False, indent=1), encoding="utf-8")
run_job(HERE, S, ink, ROOMS, ORDER, (310, 1150), (70, 20, 940, 1240), wall_px=10, label_boxes=[], keep_src=True,
        closures=[(203, 903, 288, 927)])
# fond blanc (le papier du plan source est gris chaud)
P = Image.open(HERE / "plan.png").convert("RGB")
arr = np.asarray(P).astype(float)
paper = np.median(arr[:25, :25].reshape(-1, 3), axis=0)
paper = np.maximum(paper, 200)
arr = np.clip(arr * (255.0 / paper), 0, 255)
Image.fromarray(arr.astype(np.uint8)).save(HERE / "plan.png")
