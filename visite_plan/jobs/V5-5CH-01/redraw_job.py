"""V5-5CH-01 : rendu réaliste conservé (déjà au style WooPlans), étiquettes WooPlans, pièces recalées, trajets par les portes."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import run_job

src = Image.open(HERE / "source.png").convert("RGB")
a = np.asarray(src).astype(int)
ink = (a.mean(-1) < 105) & ((a.max(-1) - a.min(-1)) < 40)
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
LABELS = [(190, 252, 120, 24), (326, 131, 44, 22), (405, 131, 44, 22), (570, 251, 120, 24), (840, 238, 120, 24),
          (870, 329, 44, 22), (184, 361, 110, 24), (481, 392, 60, 24), (863, 425, 100, 24), (802, 545, 100, 24),
          (979, 595, 26, 80), (310, 602, 100, 50), (555, 688, 160, 24), (143, 736, 44, 22), (538, 866, 90, 24),
          (377, 887, 84, 22), (782, 975, 90, 24), (390, 1046, 44, 22), (482, 1102, 40, 22), (212, 1070, 200, 24),
          (648, 1117, 100, 24)]
ROOMS = [   # seed : point dans la pièce (remplissage entre les murs) ; box : limite des pièces ouvertes
    dict(name="Véranda", label="Véranda", poly=R(505, 1050, 800, 1195), label_xy=(648, 1117), stop=(640, 1110)),
    dict(name="Entrée", label="Entrée", seed=(530, 900), box=(455, 720, 600, 1045), label_xy=(538, 866), stop=(540, 930)),
    dict(name="Séjour", label="Séjour", seed=(780, 900), box=(600, 765, 985, 1050), label_xy=(782, 975), stop=(720, 870)),
    dict(name="Salle à manger", label="Salle à manger", seed=(560, 600), box=(430, 456, 685, 720), label_xy=(565, 688), size=21,
         stop=(560, 640)),
    dict(name="Cuisine", label="Cuisine", seed=(800, 600), label_xy=(802, 545), stop=(800, 560)),
    dict(name="Hall", label="Hall", seed=(540, 390), box=(270, 300, 700, 456), label_xy=(481, 392), stop=(500, 385)),
    dict(name="Chambre 5", label="Chambre 5", seed=(860, 200), label_xy=(840, 238), stop=(820, 200)),
    dict(name="Chambre 4", label="Chambre 4", seed=(600, 200), label_xy=(570, 251), stop=(580, 200)),
    dict(name="Chambre 3", label="Chambre 3", seed=(150, 200), label_xy=(190, 252), stop=(200, 200)),
    dict(name="Chambre 2", label="Chambre 2", seed=(200, 600), label_xy=(300, 602), stop=(220, 600)),
    dict(name="Chambre parentale", label="Chambre parentale", seed=(180, 940), label_xy=(200, 1070), size=22, stop=(220, 900)),
    dict(name="Buanderie", label="Buanderie", seed=(180, 380), label_xy=(184, 361), size=21),
    dict(name="Magasin", label="Magasin", seed=(880, 440), label_xy=(863, 425), size=20),
    dict(name="Sortie", label="Sortie", seed=(980, 600), label_xy=(980, 600), size=18),
    dict(name="Dressing", label="Dressing", seed=(380, 860), label_xy=(377, 887), size=17),
    dict(name="WC ch3", label="WC", seed=(320, 140), size=18), dict(name="WC ch4", label="WC", seed=(410, 140), size=18),
    dict(name="WC ch5", label="WC", seed=(870, 340), size=18), dict(name="WC ch2", label="WC", seed=(140, 750), size=18),
    dict(name="WC parental", label="WC", seed=(390, 1060), size=18), dict(name="WC entrée", label="WC", seed=(480, 1105), size=17),
]
ORDER = ["Véranda", "Entrée", "Séjour", "Salle à manger", "Cuisine", "Hall", "Chambre 5", "Chambre 4", "Chambre 3",
         "Chambre 2", "Chambre parentale"]
run_job(HERE, src, ink, ROOMS, ORDER, (650, 1185), (30, 30, 1050, 1310), wall_px=12, label_boxes=LABELS, keep_src=True,
        closures=[(926, 480, 936, 705)])
