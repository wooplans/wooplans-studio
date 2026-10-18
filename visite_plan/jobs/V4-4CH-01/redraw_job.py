"""V4-4CH-01 : plan source (sols éclaircis en blanc) conservé, étiquettes WooPlans, pièces recalées, trajets par les portes."""
import sys
from pathlib import Path
import numpy as np
from PIL import Image
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1] / "tools"))
from redraw import run_job

src = Image.open(HERE / "source.png").convert("RGB")
a = np.asarray(src).astype(int)
ink = (a.mean(-1) < 110) & ((a.max(-1) - a.min(-1)) < 40)
R = lambda x0, y0, x1, y1: [(x0, y0), (x1, y0), (x1, y1), (x0, y1)]
ROOMS = [
    dict(name="Porche d'entrée", label="Porche d'entrée", poly=R(430, 795, 775, 900), label_xy=(532, 852), stop=(530, 850)),
    dict(name="Entrée", label="Entrée", seed=(477, 664), box=(428, 468, 535, 795), stop=(480, 640)),
    dict(name="Séjour", label="Séjour", seed=(650, 600), box=(535, 465, 792, 795), stop=(600, 640)),
    dict(name="Hall", label="Hall", seed=(375, 436), box=(215, 393, 1062, 468), stop=(420, 430)),
    dict(name="Salle à manger", label="Salle à\nmanger", seed=(537, 303), box=(450, 195, 625, 395), stop=(537, 330)),
    dict(name="Cuisine", label="Cuisine", seed=(337, 300), box=(215, 150, 455, 395), label_xy=(337, 235), stop=(340, 320)),
    dict(name="Bureau", label="Bureau", seed=(360, 556), box=(290, 460, 425, 682), stop=(360, 540)),
    dict(name="Chambre 2", label="Chambre 2", seed=(708, 322), stop=(700, 330)),
    dict(name="Chambre 4", label="Chambre 4", seed=(885, 292), box=(810, 140, 1015, 392), stop=(880, 300)),
    dict(name="Chambre 3", label="Chambre 3", seed=(900, 670), stop=(880, 560)),
    dict(name="Chambre parentale", label="Chambre\nparentale", seed=(240, 627), stop=(220, 600)),
    dict(name="Buanderie", label="Buanderie", seed=(112, 124), size=20),
    dict(name="Porche arrière", label="Porche arrière", seed=(337, 126), size=20),
    dict(name="Cellier", label="Cellier", seed=(120, 226), size=20),
    dict(name="SDB", label="SDB", seed=(132, 355), size=20),
    dict(name="Dressing", label="Dressing", seed=(102, 447), size=17),
    dict(name="WC", label="WC", seed=(1002, 427), size=17),
    dict(name="SDB 3", label="SDB", seed=(964, 520), size=17),
    dict(name="Terrasse", label="Terrasse", poly=R(60, 770, 430, 830), label_xy=(150, 800), size=20),
    dict(name="Attente", label="Attente", seed=(661, 840), label_xy=(661, 805), size=17),
]
ORDER = ["Porche d'entrée", "Entrée", "Séjour", "Hall", "Salle à manger", "Cuisine", "Bureau", "Chambre 2", "Chambre 4",
         "Chambre 3", "Chambre parentale"]
run_job(HERE, src, ink, ROOMS, ORDER, (600, 885), (0, 0, 1080, 1030), wall_px=10, keep_src=True)
