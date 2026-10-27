"""V3-3CH-02 : plan couleur conservé (proche du style WooPlans), étiquettes WooPlans, pièces recalées, trajets par les portes."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import run_job

src = Image.open(HERE / "source.png").convert("RGB")
a = np.asarray(src).astype(int)
ink = (a.mean(-1) < 125) & ((a.max(-1) - a.min(-1)) < 30)
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
LABELS = [(392, 134, 120, 26), (389, 272, 100, 26), (558, 245, 120, 26), (858, 239, 120, 26), (585, 543, 190, 26),
          (830, 378, 50, 26), (830, 506, 50, 26), (350, 477, 76, 48), (222, 666, 190, 26), (537, 833, 90, 26),
          (867, 732, 110, 50), (993, 768, 26, 100), (726, 1030, 100, 48)]
ROOMS = [
    dict(name="Porche d'entrée", label="Porche\nd'entrée", poly=R(555, 895, 790, 1085), label_xy=(726, 1030), stop=(690, 1000)),
    dict(name="Séjour", label="Séjour", seed=(537, 760), box=(392, 565, 685, 990), label_xy=(537, 833), stop=(540, 720)),
    dict(name="Salle à manger", label="Salle à manger", seed=(585, 450), box=(445, 300, 675, 562), label_xy=(585, 543),
         size=22, stop=(560, 470)),
    dict(name="Cuisine", label="Cuisine", seed=(389, 300), box=(265, 160, 445, 380), label_xy=(389, 272), stop=(400, 300)),
    dict(name="Buanderie", label="Buanderie", seed=(392, 120), label_xy=(392, 134), size=21, stop=(390, 115)),
    dict(name="Garage", label="Garage", poly=R(60, 648, 392, 980), label_xy=(222, 666), stop=(260, 740)),
    dict(name="Chambre 3", label="Chambre 3", seed=(600, 180), label_xy=(558, 245), stop=(600, 200)),
    dict(name="Chambre 2", label="Chambre 2", seed=(830, 180), label_xy=(858, 239), stop=(830, 200)),
    dict(name="SDB", label="SDB", poly=R(762, 300, 900, 560), label_xy=(830, 378), size=21, stop=(800, 380)),
    dict(name="SDB 2", label="SDB", seed=(830, 506), size=21),
    dict(name="Chambre parentale", label="Chambre\nparentale", seed=(860, 780), box=(675, 640, 952, 892), label_xy=(867, 732), stop=(820, 760)),
    dict(name="Porche arrière", label="Porche\narrière", seed=(350, 477), label_xy=(350, 477), size=18),
    dict(name="Terrasse", poly=R(950, 640, 1030, 885)),
    dict(name="Dégagement", poly=R(242, 572, 392, 656)),
    dict(name="WC garage", label="WC", poly=R(45, 578, 240, 646), size=18),
]
ORDER = ["Porche d'entrée", "Séjour", "Salle à manger", "Cuisine", "Buanderie", "Garage", "Chambre 3", "Chambre 2", "SDB",
         "Chambre parentale"]
run_job(HERE, src, ink, ROOMS, ORDER, (726, 1080), (30, 30, 1060, 1110), wall_px=10, label_boxes=LABELS, keep_src=True,
        openings=[(325, 630, 380, 672), (368, 552, 412, 650)], closures=[(944, 640, 954, 890), (300, 562, 392, 572)])
