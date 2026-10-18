"""Pièces (polygones) et trajets du point pour V5-5CH-01 : coordonnées en pixels du plan nettoyé (1080x1343), décalées (OFF) vers plan.png."""
import json
from PIL import Image, ImageDraw
OFF = (-30, -30)
def o(p): return (p[0]+OFF[0], p[1]+OFF[1])
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
POLYS = {
 "Véranda": rect(515,1050,800,1195),
 "Entrée": rect(490,780,590,1040),
 "Séjour": rect(605,770,970,1035),
 "Salle à manger": rect(445,455,690,705),
 "Cuisine": rect(695,490,925,705),
 "Hall": rect(290,300,690,450),
 "Chambre 5": rect(700,60,965,285),
 "Chambre 4": rect(370,60,690,300),
 "Chambre 3": rect(75,60,290,300),
 "Chambre 2": rect(100,455,360,690),
 "Chambre parentale": [(75,800),(265,800),(265,785),(450,785),(450,1130),(325,1130),(325,1100),(75,1100)],
}
START = (650, 1235)
PATHS = {   # waypoints : toujours par les portes / ouvertures
 "Véranda": [START, (650,1150), (640,1110)],
 "Entrée": [(640,1110),(600,1080),(560,1048),(545,1000),(540,930)],
 "Séjour": [(540,930),(570,860),(600,850),(680,850),(720,870)],
 "Salle à manger": [(720,870),(640,800),(600,760),(590,720),(560,695)],
 "Cuisine": [(560,695),(620,690),(670,640),(690,560),(760,530),(800,525)],
 "Hall": [(800,525),(720,560),(680,570),(600,520),(560,470),(540,420),(500,385)],
 "Chambre 5": [(500,385),(600,380),(670,370),(710,350),(735,320),(760,280),(820,200)],
 "Chambre 4": [(820,200),(760,280),(735,320),(700,340),(610,330),(505,310),(500,280),(560,180)],
 "Chambre 3": [(560,180),(500,280),(505,315),(400,330),(320,320),(300,280),(200,190)],
 "Chambre 2": [(200,190),(300,280),(320,320),(390,360),(405,450),(410,600),(410,710),(330,712),(300,670),(200,590)],
 "Chambre parentale": [(200,590),(300,670),(330,712),(400,720),(400,760),(300,770),(285,810),(220,900)],
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
