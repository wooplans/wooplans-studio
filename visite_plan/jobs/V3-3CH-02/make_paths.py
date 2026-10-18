"""Pièces et trajets pour V3-3CH-02 : coordonnées du plan source (avant agrandissement x1.5), puis échelle K et décalage OFF vers plan.png."""
import json
from PIL import Image, ImageDraw
K = 1.5
OFF = (-20, -25)
def o(p): return (p[0]*K+OFF[0], p[1]*K+OFF[1])
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
POLYS = {
 "Porche d'entrée": rect(365, 650, 520, 720),
 "Séjour": rect(265, 380, 450, 653),
 "Salle à manger": rect(265, 200, 450, 376),
 "Cuisine": rect(180, 110, 330, 247),
 "Buanderie": rect(205, 65, 295, 100),
 "Garage": rect(40, 433, 265, 653),
 "Chambre 3": rect(330, 45, 475, 170),
 "Chambre 2": rect(480, 45, 630, 170),
 "SDB": rect(505, 200, 600, 370),
 "Chambre parentale": rect(455, 430, 690, 590),
}
START = (440, 715)
PATHS = {   # waypoints : toujours par les portes / ouvertures
 "Porche d'entrée": [START,(440,690)],
 "Séjour": [(440,690),(470,665),(462,628),(430,600),(370,520),(360,500)],
 "Salle à manger": [(360,500),(345,420),(345,378),(330,330),(330,300)],
 "Cuisine": [(330,300),(300,250),(270,210),(255,185)],
 "Buanderie": [(255,185),(285,140),(305,112),(305,92),(270,84)],
 "Garage": [(270,84),(305,112),(320,200),(330,330),(345,378),(300,395),(268,405),(232,405),(232,445),(150,520),(132,540)],
 "Chambre 3": [(132,540),(150,520),(232,445),(232,405),(268,405),(345,378),(420,330),(470,250),(470,180),(455,158),(400,120)],
 "Chambre 2": [(400,120),(455,158),(480,165),(520,160),(560,110)],
 "SDB": [(560,110),(520,160),(480,180),(480,265),(510,268),(550,240)],
 "Chambre parentale": [(550,240),(510,268),(480,265),(480,420),(475,442),(520,480),(560,490)],
}
def chaikin(pts, n=2):
    for _ in range(n):
        out=[pts[0]]
        for a,b in zip(pts,pts[1:]):
            out += [(0.75*a[0]+0.25*b[0],0.75*a[1]+0.25*b[1]),(0.25*a[0]+0.75*b[0],0.25*a[1]+0.75*b[1])]
        out.append(pts[-1]); pts=out
    return pts
rooms=[]
for name, wp in PATHS.items():
    sm = chaikin(wp) if len(wp)>2 else wp
    rooms.append({"name":name,"path":[[round(c,1) for c in o(p)] for p in sm],"poly":[[round(c,1) for c in o(p)] for p in POLYS[name]]})
json.dump({"start":list(o(START)),"rooms":rooms},open("paths.json","w"),indent=1,ensure_ascii=False)
img=Image.open("plan.png").convert("RGB"); d=ImageDraw.Draw(img,"RGBA")
cols=[(240,138,46),(200,0,0),(0,160,0),(160,0,200),(0,160,160),(200,120,0),(255,0,120),(90,90,90),(0,0,0),(0,120,255)]
for i,r in enumerate(rooms):
    c=cols[i%len(cols)]
    d.polygon([tuple(p) for p in r["poly"]],fill=c+(45,),outline=c+(255,))
    d.line([tuple(p) for p in r["path"]],fill=c+(255,),width=5)
img.save("paths_check.png")
