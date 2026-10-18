"""Pièces et trajets pour V4-4CH-02 : coordonnées du plan source (avant agrandissement x1), puis échelle K et décalage OFF vers plan.png."""
import json
from PIL import Image, ImageDraw
K = 1
OFF = (-20, -40)
def o(p): return (p[0]*K+OFF[0], p[1]*K+OFF[1])
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
POLYS = {
 "Porche d'entrée": rect(318, 915, 540, 1030),
 "Salon": rect(330, 455, 725, 905),
 "Salle à manger": rect(555, 220, 725, 445),
 "Cuisine": rect(335, 90, 540, 340),
 "Porche arrière": rect(560, 105, 870, 205),
 "Chambre 1": rect(95, 115, 305, 320),
 "WC": rect(40, 340, 160, 630),
 "Chambre 2": rect(95, 645, 305, 905),
 "Chambre 3": rect(750, 215, 990, 435),
 "Chambre parentale": [(750,540),(1045,540),(1045,715),(985,715),(985,1025),(750,1025)],
}
START = (430, 1080)
PATHS = {   # waypoints : toujours par les portes / ouvertures
 "Porche d'entrée": [START,(430,1040),(425,980)],
 "Salon": [(425,980),(380,935),(362,900),(360,780),(380,720),(420,718),(500,720)],
 "Salle à manger": [(500,720),(420,718),(365,700),(360,500),(450,470),(600,460),(640,425)],
 "Cuisine": [(640,425),(600,455),(520,452),(515,420),(500,360),(440,250)],
 "Porche arrière": [(440,250),(500,240),(540,180),(580,165),(700,150)],
 "Chambre 1": [(700,150),(580,165),(545,180),(480,250),(500,380),(515,440),(400,470),(330,470),(280,400),(275,340),(220,260)],
 "WC": [(220,260),(275,340),(250,420),(200,430),(150,415),(110,410)],
 "Chambre 2": [(110,410),(200,430),(260,520),(270,620),(250,665),(200,770)],
 "Chambre 3": [(200,770),(250,665),(280,600),(330,480),(400,462),(700,460),(745,430),(780,400),(820,330)],
 "Chambre parentale": [(820,330),(780,410),(760,470),(760,600),(765,700),(800,760),(800,850)],
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
