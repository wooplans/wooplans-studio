"""V3-3CH-03 : croquis bleu redessiné au style WooPlans (murs, portes et pièces relevés à la main sur le plan,
mobilier repris en gris), étiquettes WooPlans, trajets par les portes."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import run_job

S = Image.open(HERE / "source_fr.png").convert("RGB")
a = np.asarray(S).astype(int)
ink = ((a[..., 2] - a[..., 0]) > 60) & (a.mean(-1) < 200)
TEXT = [(322, 224, 140, 26), (809, 261, 140, 26), (764, 612, 140, 26), (348, 430, 90, 56), (442, 435, 30, 110),
        (705, 425, 130, 26), (900, 420, 130, 26), (210, 478, 110, 26), (330, 792, 160, 26), (523, 827, 80, 26),
        (718, 870, 90, 56), (318, 1008, 90, 26), (432, 529, 100, 22), (586, 650, 26, 90), (715, 475, 70, 24)]
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
ROOMS = [
    dict(name="Entrée", label="Entrée", poly=[(472, 712), (775, 712), (775, 770), (565, 770), (565, 975), (472, 975)],
         label_xy=(518, 860), size=21, stop=(515, 900)),
    dict(name="Salon", label="Salon", poly=R(105, 870, 472, 1300), label_xy=(318, 960), stop=(330, 1000)),
    dict(name="Salle à manger", label="Salle à manger", poly=R(160, 712, 472, 870), label_xy=(316, 845), size=22,
         stop=(250, 760)),
    dict(name="Entrée latérale", label="Entrée", poly=R(105, 340, 290, 640), label_xy=(200, 478), stop=(200, 520)),
    dict(name="Salle de bain", label="Salle\nde bain", poly=[(290, 345), (415, 345), (415, 505), (385, 505), (385, 545),
                                                            (290, 545)], sol="eau", label_xy=(345, 440), size=20,
         stop=(340, 470)),
    dict(name="Chambre 1", label="Chambre 1", poly=R(205, 55, 440, 340), label_xy=(322, 224), stop=(320, 250)),
    dict(name="Chambre 2", label="Chambre 2", poly=R(690, 90, 940, 375), label_xy=(809, 261), stop=(800, 280)),
    dict(name="Salle de bain 2", label="Salle\nde bain", poly=R(660, 770, 775, 975), sol="eau", label_xy=(718, 870), size=19,
         stop=(715, 820)),
    dict(name="Chambre 3", label="Chambre 3", poly=[(555, 495), (1005, 495), (1005, 765), (775, 765), (775, 712), (555, 712)],
         label_xy=(764, 612), stop=(680, 610)),
    dict(name="Couloir", poly=[(440, 240), (690, 240), (690, 375), (555, 375), (555, 712), (160, 712), (160, 640), (290, 640),
                               (290, 545), (385, 545), (385, 505), (475, 505), (475, 375), (440, 375)]),
    dict(name="WC 1", label="WC", poly=R(440, 55, 540, 240), sol="eau", size=18),
    dict(name="WC 2", label="WC", poly=R(585, 55, 690, 240), sol="eau", size=18),
    dict(name="Rangement", poly=R(415, 345, 475, 505)),
    dict(name="Rangement 3", label="Rangement", poly=R(555, 375, 785, 495), label_xy=(690, 430), size=17),
    dict(name="Salle de bain 3", label="Salle de bain", poly=R(785, 375, 1005, 495), sol="eau", size=16),
    dict(name="Rangement entrée", poly=R(565, 770, 660, 975)),
]
for r in ROOMS:
    r["fixe"] = True
DOORS = [(515, 975, 60), (472, 925, 56), (300, 870, 290), (235, 712, 140), (225, 640, 136), (290, 592, 86), (290, 480, 50),
         (172, 340, 56), (440, 300, 56), (440, 190, 46), (690, 335, 56), (690, 200, 46), (555, 545, 56), (785, 450, 44),
         (690, 495, 56), (515, 712, 64), (725, 770, 50), (475, 440, 40)]
ORDER = ["Entrée", "Salon", "Salle à manger", "Entrée latérale", "Salle de bain", "Chambre 1", "Chambre 2", "Salle de bain 2",
         "Chambre 3"]
run_job(HERE, S, ink, ROOMS, ORDER, (515, 968), (60, 20, 1049, 1340), wall_px=14, T=22, auto_gaps=False, portes=DOORS,
        furn_col=(140, 140, 138), label_boxes=TEXT)
