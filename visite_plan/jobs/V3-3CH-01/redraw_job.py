"""V3-3CH-01 : plan redessiné au style WooPlans, pièces recalées sur les murs, trajets par les portes."""
import sys
from pathlib import Path
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import run_job, blue_ink

src = Image.open(HERE / "source.png").convert("RGB")
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
LABELS = [(275, 322, 160, 34), (715, 322, 160, 34), (220, 510, 110, 66), (1050, 497, 130, 34), (638, 711, 110, 34),
          (345, 860, 150, 66), (1010, 898, 200, 34), (738, 1048, 110, 34), (472, 200, 50, 28), (1088, 307, 120, 26)]
ROOMS = [
    dict(name="Porche", label="Porche", poly=R(535, 965, 905, 1165), sol="ext", ouvert=True, stop=(735, 1060)),
    dict(name="Séjour", label="Séjour", poly=R(432, 530, 885, 965), stop=(640, 750)),
    dict(name="Salle à manger", label="Salle à manger", poly=R(885, 645, 1140, 935), label_xy=(1010, 898), stop=(905, 795)),
    dict(name="Cuisine", label="Cuisine", poly=R(985, 375, 1215, 645), sol="cuisine", stop=(1060, 520)),
    dict(name="Buanderie", label="Buanderie", poly=R(985, 240, 1215, 375), sol="eau", label_xy=(1110, 312), size=20, stop=(1030, 320)),
    dict(name="Couloir", poly=[(355, 410), (440, 410), (440, 305), (560, 305), (560, 410), (890, 410), (890, 180), (985, 180),
                               (985, 645), (885, 645), (885, 530), (432, 530), (432, 560), (355, 560)]),
    dict(name="Chambre 2", label="Chambre 2", poly=R(560, 55, 890, 410), label_xy=(715, 330), stop=(720, 280)),
    dict(name="WC", label="WC", poly=R(440, 55, 560, 305), sol="eau", label_xy=(475, 205), size=20, stop=(500, 230)),
    dict(name="Chambre 1", label="Chambre 1", poly=R(120, 55, 440, 410), label_xy=(275, 330), stop=(300, 280)),
    dict(name="Salle de bain", label="Salle\nde bain", poly=R(55, 420, 345, 578), sol="eau", label_xy=(225, 505), size=21),
    dict(name="Dressing", poly=R(55, 578, 345, 712)),
    dict(name="Chambre principale", label="Chambre\nprincipale", poly=[(95, 712), (345, 712), (345, 560), (432, 560), (432, 1065), (95, 1065)],
         label_xy=(330, 860), stop=(290, 790)),
]
ORDER = ["Porche", "Séjour", "Salle à manger", "Cuisine", "Buanderie", "Chambre 2", "WC", "Chambre 1", "Chambre principale"]
run_job(HERE, src, blue_ink(src), ROOMS, ORDER, (735, 1150), (10, 30, 1260, 1180), label_boxes=LABELS, ext_doors=[(940, 180)],
        portes=[(478, 305, 56), (392, 560, 60)])
