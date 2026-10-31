"""V3-014 : plan de distribution du catalogue conservé (fond blanc, murs noirs), noms anglais remplacés par des
étiquettes WooPlans en français, surfaces du plan (S=…) conservées, pièces recalées, trajets par les portes."""
import sys
from pathlib import Path
import cv2
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import run_job

src = Image.open(HERE / "source.png").convert("RGB")
a = np.asarray(src).astype(int)
# noms des pièces (rouge, « Bedroom (Chambre) 2 »…) : effacés, les dimensions (bleu) restent
red = (a[..., 0] > 150) & (a[..., 1] < 140) & (a[..., 2] < 140) & (a[..., 0] - a[..., 1] > 60)
NAMES = [(895, 118, 152, 20), (154, 219, 171, 20), (573, 229, 171, 20), (1155, 247, 128, 20), (415, 254, 99, 20),
         (896, 287, 129, 20), (690, 468, 140, 20), (1134, 468, 161, 20), (214, 495, 97, 20), (380, 718, 142, 40),
         (694, 727, 115, 20), (168, 762, 75, 20), (1032, 817, 109, 20), (628, 1000, 149, 20)]
txt = np.zeros(red.shape, bool)
for x, y, w, h in NAMES:
    txt[y - 2:y + h + 2, x - 2:x + w + 2] = True
kill = cv2.dilate((red & txt).astype(np.uint8), np.ones((3, 3), np.uint8)).astype(bool)
b = np.asarray(src).copy(); b[kill] = 255
b[0:20, 0:90] = 255                                   # reste du titre « …ACES » en haut à gauche
src = Image.fromarray(b)
a = b.astype(int)
ink = (a.mean(-1) < 110) & ((a.max(-1) - a.min(-1)) < 40)

R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
ROOMS = [
    dict(name="Terrasse 1", label="Terrasse", poly=R(514, 946, 900, 1088), label_xy=(707, 990), size=22, stop=(707, 1030)),
    dict(name="Salle à manger", label="Salle à manger", poly=R(622, 548, 910, 940), label_xy=(765, 718), size=22,
         stop=(760, 880)),
    dict(name="Salon", label="Salon", poly=R(918, 548, 1290, 1083), label_xy=(1086, 808), stop=(1000, 800)),
    dict(name="Cuisine", label="Cuisine", poly=R(800, 192, 1134, 424), label_xy=(960, 278), stop=(940, 380)),
    dict(name="Magasin", label="Magasin", poly=R(1148, 97, 1290, 424), label_xy=(1219, 238), size=22, stop=(1210, 360)),
    dict(name="Terrasse 2", label="Terrasse", poly=R(800, 90, 1134, 180), label_xy=(970, 110), size=20, stop=(860, 135)),
    dict(name="Couloir", label="Couloir", poly=[(366, 352), (540, 352), (540, 438), (1134, 438), (1134, 530),
                                               (366, 530)], label_xy=(760, 462), size=22, stop=(700, 495)),
    dict(name="WC visiteurs", label="WC", poly=R(1148, 440, 1290, 530), label_xy=(1215, 465), size=18, stop=(1190, 505)),
    dict(name="Chambre 3", label="Chambre 3", poly=R(556, 97, 783, 424), label_xy=(660, 222), stop=(640, 380)),
    dict(name="SDB 2", label="SDB", poly=R(365, 97, 540, 345), label_xy=(462, 245), size=20, stop=(500, 320)),
    dict(name="Chambre 2", label="Chambre 2", poly=R(122, 97, 350, 424), label_xy=(238, 212), stop=(280, 380)),
    dict(name="SDB 1", label="SDB", poly=R(122, 438, 350, 612), label_xy=(262, 486), size=20, stop=(300, 560)),
    dict(name="Chambre parentale", label="Chambre\nparentale", poly=[(365, 545), (608, 545), (608, 940), (300, 940),
         (300, 628), (365, 628)], label_xy=(450, 715), size=22, stop=(420, 820)),
    dict(name="Dressing", label="Dressing", poly=R(122, 628, 288, 940), label_xy=(205, 752), size=20, stop=(220, 860)),
]
ORDER = ["Terrasse 1", "Salle à manger", "Salon", "Cuisine", "Magasin", "Terrasse 2", "Couloir", "WC visiteurs",
         "Chambre 3", "SDB 2", "Chambre 2", "SDB 1", "Chambre parentale", "Dressing"]
run_job(HERE, src, ink, ROOMS, ORDER, (706, 1078), (90, 0, 1318, 1188), wall_px=10, keep_src=True, fp_close=300,
        closures=[(625, 934, 800, 960), (940, 178, 1050, 197)])   # fenêtres de la salle à manger et de la cuisine
