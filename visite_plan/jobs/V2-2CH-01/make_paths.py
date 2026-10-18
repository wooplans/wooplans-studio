"""Pièces (polygones) et trajets du point pour V2-2CH-01 : coordonnées en pixels de l'image d'origine (1170x1344), décalées (OFF) vers plan.png."""
import json
from PIL import Image, ImageDraw
OFF = (-40, -50)
def o(p): return (p[0]+OFF[0], p[1]+OFF[1])
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
POLYS = {
 "Véranda": rect(108,922,488,1092),
 "Séjour": rect(108,482,492,905),
 "Salle à manger": [(515,470),(868,470),(868,705),(600,705),(600,800),(515,800)],
 "Cuisine": rect(645,140,880,455),
 "Sortie de service": rect(898,478,1045,700),
 "Buanderie": rect(898,140,1040,462),
 "Chambre 2": [(135,140),(485,140),(485,365),(605,365),(605,455),(135,455)],
 "WC": rect(517,140,615,340),
 "Chambre parentale": [(612,718),(1045,718),(1045,1085),(630,1085),(630,890),(612,890)],
 "WC privé": rect(515,830,600,1060),
}
START = (320, 1170)
PATHS = {   # waypoints : toujours par les portes / ouvertures
 "Véranda": [START, (318,1080), (325,1010)],
 "Séjour": [(325,1010),(420,960),(450,925),(450,880),(400,790),(300,700)],
 "Salle à manger": [(300,700),(420,620),(505,595),(560,590)],
 "Cuisine": [(560,590),(600,510),(680,470),(745,430),(750,395)],
 "Sortie de service": [(750,395),(760,470),(840,540),(880,598),(930,610),(965,650)],
 "Buanderie": [(965,650),(995,570),(1003,490),(1003,445),(955,390)],
 "Chambre 2": [(955,390),(1003,445),(1000,520),(930,605),(880,605),(845,680),(720,688),(600,682),(562,620),(566,485),(565,425),(490,410),(390,340),(300,300)],
 "WC": [(300,300),(420,325),(470,318),(530,305),(555,240)],
 "Chambre parentale": [(555,240),(510,318),(470,330),(480,405),(565,425),(568,490),(558,600),(560,700),(565,752),(612,756),(700,790),(720,805)],
 "WC privé": [(720,805),(625,820),(612,860),(570,870),(560,935)],
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
    rooms.append({"name":name,"path":[[round(c,1) for c in o(p)] for p in sm],"poly":[list(o(p)) for p in POLYS[name]]})
json.dump({"start":list(o(START)),"rooms":rooms},open("paths.json","w"),indent=1,ensure_ascii=False)
img=Image.open("plan.png").convert("RGB"); d=ImageDraw.Draw(img,"RGBA")
cols=[(240,138,46),(200,0,0),(0,160,0),(160,0,200),(0,160,160),(200,120,0),(255,0,120),(90,90,90),(0,0,0),(0,120,255)]
for i,r in enumerate(rooms):
    c=cols[i%len(cols)]
    d.polygon([tuple(p) for p in r["poly"]],fill=c+(45,),outline=c+(255,))
    d.line([tuple(p) for p in r["path"]],fill=c+(255,),width=5)
img.save("paths_check.png")
