"""Pièces et trajets pour V4-4CH-01 : coordonnées du plan source (avant agrandissement x1.5), puis échelle K et décalage OFF vers plan.png."""
import json
from PIL import Image, ImageDraw
K = 1.5
OFF = (-5, 0)
def o(p): return (p[0]*K+OFF[0], p[1]*K+OFF[1])
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
POLYS = {
 "Porche d'entrée": rect(280, 547, 515, 600),
 "Entrée": rect(290, 320, 345, 533),
 "Séjour": rect(350, 315, 515, 525),
 "Hall": rect(150, 260, 707, 313),
 "Salle à manger": rect(305, 140, 410, 255),
 "Cuisine": rect(150, 100, 300, 255),
 "Bureau": rect(195, 315, 280, 455),
 "Chambre 2": rect(415, 55, 535, 255),
 "Chambre 4": rect(545, 100, 680, 250),
 "Chambre 3": rect(520, 320, 680, 525),
 "Chambre parentale": rect(25, 345, 185, 510),
}
START = (400, 670)
PATHS = {   # waypoints : toujours par les portes / ouvertures
 "Porche d'entrée": [START,(400,615),(380,575)],
 "Entrée": [(380,575),(330,540),(318,520),(318,470)],
 "Séjour": [(318,470),(330,440),(360,425),(400,430)],
 "Hall": [(400,430),(330,420),(318,360),(318,300),(250,290)],
 "Salle à manger": [(250,290),(300,288),(355,270),(358,252)],
 "Cuisine": [(358,252),(330,240),(305,230),(260,215),(180,215)],
 "Bureau": [(180,215),(200,245),(230,262),(240,290),(230,320),(225,360)],
 "Chambre 2": [(225,360),(230,320),(240,295),(350,290),(500,288),(515,262),(490,230),(470,215)],
 "Chambre 4": [(470,215),(500,250),(520,262),(560,265),(565,240),(590,200)],
 "Chambre 3": [(590,200),(565,245),(560,280),(540,300),(530,330),(560,380)],
 "Chambre parentale": [(560,380),(530,330),(530,295),(400,290),(250,292),(185,300),(170,335),(150,370),(130,400)],
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
