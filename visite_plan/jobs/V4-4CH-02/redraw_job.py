"""V4-4CH-02 : capture floue redessinée au style WooPlans (murs, portes et pièces relevés à la main sur la capture,
mobilier repris en gris), étiquettes WooPlans, trajets par les portes."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import run_job
from relabel import erase_text

S = Image.open(HERE / "source_fr.png").convert("RGB")
OLD = [(180, 272, 62, 13), (435, 218, 50, 13), (717, 145, 74, 12), (643, 333, 32, 20), (887, 384, 62, 13), (408, 396, 54, 11),
       (98, 400, 40, 21), (97, 494, 22, 11), (98, 588, 40, 21), (985, 500, 54, 11), (865, 632, 46, 11), (982, 645, 48, 21),
       (560, 718, 38, 13), (196, 727, 62, 13), (860, 760, 90, 13), (435, 973, 54, 23)]
for x, y, hw, hh in OLD:
    S = erase_text(S, x, y, hw, hh, dark=215, maxh=34, grow=9)
a = np.asarray(S).astype(float)
ink = ((a[..., 2] - a[..., 0]) > 70) & (a.mean(-1) < 200)
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
ROOMS = [
    dict(name="Porche d'entrée", label="Porche d'entrée", poly=R(318, 910, 545, 1035), ouvert=True, sol="ext", label_xy=(435, 980),
         size=22, stop=(380, 960)),
    dict(name="Salon", label="Salon", poly=R(318, 450, 740, 910), label_xy=(560, 718), stop=(450, 700)),
    dict(name="Salle à manger", label="Salle à\nmanger", poly=R(545, 210, 740, 450), label_xy=(643, 333), stop=(640, 400)),
    dict(name="Cuisine", label="Cuisine", poly=R(318, 85, 545, 345), label_xy=(435, 218), sol="cuisine", stop=(470, 260)),
    dict(name="Porche arrière", label="Porche arrière", poly=R(545, 100, 880, 210), ouvert=True, sol="ext", label_xy=(717, 150),
         size=21, stop=(640, 160)),
    dict(name="Chambre 1", label="Chambre 1", poly=R(85, 105, 318, 345), label_xy=(190, 272), stop=(200, 260)),
    dict(name="WC", label="WC", poly=R(38, 345, 240, 640), sol="eau", label_xy=(110, 494), size=20, stop=(200, 490)),
    dict(name="Chambre 2", label="Chambre 2", poly=R(85, 640, 318, 915), label_xy=(196, 760), stop=(200, 760)),
    dict(name="Chambre 3", label="Chambre 3", poly=R(740, 215, 1000, 450), label_xy=(887, 384), stop=(860, 360)),
    dict(name="Chambre parentale", label="Chambre\nparentale", poly=R(740, 715, 990, 1030), label_xy=(865, 880), stop=(830, 820)),
    dict(name="Rangement", label="Rangement", poly=R(318, 345, 490, 450), label_xy=(404, 398), size=17),
    dict(name="Couloir", poly=[(240, 345), (318, 345), (318, 640), (240, 640)]),
    dict(name="Couloir 2", poly=[(740, 450), (918, 450), (918, 535), (812, 535), (812, 715), (740, 715)]),
    dict(name="WC douche", label="WC / douche", poly=R(918, 450, 1045, 535), sol="eau", size=15),
    dict(name="Dressing", label="Dressing", poly=R(812, 535, 918, 715), size=16),
    dict(name="Salle de bain", label="Salle\nde bain", poly=R(918, 535, 1045, 715), sol="eau", size=17),
]
for r in ROOMS:
    r["fixe"] = True
DOORS = [(372, 910, 52), (545, 300, 60), (545, 165, 44), (640, 450, 150), (490, 410, 40), (275, 345, 46), (280, 640, 46),
         (240, 490, 50), (318, 488, 70), (776, 450, 52), (860, 450, 46), (812, 620, 50), (918, 620, 50), (776, 715, 56),
         (740, 488, 64)]
ORDER = ["Porche d'entrée", "Salon", "Salle à manger", "Cuisine", "Porche arrière", "Chambre 1", "WC", "Chambre 2",
         "Chambre 3", "Chambre parentale"]
run_job(HERE, S, ink, ROOMS, ORDER, (430, 1030), (10, 60, 1070, 1060), wall_px=14, T=22, auto_gaps=False, portes=DOORS,
        furn_col=(150, 150, 148))
