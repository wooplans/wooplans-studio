"""Pièces (polygones) et trajets du point pour V3-3CH-01 : coordonnées en pixels du plan nettoyé (1268x1238), décalées (OFF) vers plan.png."""
import json
from PIL import Image, ImageDraw
OFF = (-10, -30)
def o(p): return (p[0]+OFF[0], p[1]+OFF[1])
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
POLYS = {
 "Porche": rect(545,975,890,1160),
 "Séjour": rect(450,545,880,960),
 "Salle à manger": rect(890,645,1135,925),
 "Cuisine": rect(995,380,1205,630),
 "Buanderie": rect(995,255,1205,355),
 "Chambre 2": rect(570,70,880,400),
 "WC": rect(445,70,555,295),
 "Chambre 1": rect(135,70,430,400),
 "Chambre principale": [(55,425),(340,425),(340,560),(430,560),(430,1060),(95,1060),(95,715),(55,715)],
}
START = (735, 1150)
PATHS = {   # waypoints : toujours par les portes / ouvertures
 "Porche": [START, (735,1060)],
 "Séjour": [(735,1060),(790,1000),(828,962),(800,900),(720,800),(640,750)],
 "Salle à manger": [(640,750),(780,700),(870,720),(905,770),(905,795)],
 "Cuisine": [(905,795),(930,690),(935,600),(980,540),(1060,520)],
 "Buanderie": [(1060,520),(990,480),(935,420),(935,320),(975,300),(1030,320)],
 "Chambre 2": [(1030,320),(975,300),(935,330),(935,450),(890,480),(800,470),(640,460),(590,425),(588,400),(640,300),(720,280)],
 "WC": [(720,280),(640,300),(588,400),(560,440),(480,440),(470,330),(480,280),(500,230)],
 "Chambre 1": [(500,230),(480,300),(470,380),(440,425),(412,412),(400,370),(300,280)],
 "Chambre principale": [(300,280),(400,370),(412,412),(400,470),(395,560),(400,630),(385,700),(330,760),(290,790)],
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
