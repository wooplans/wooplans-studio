"""Pièces et trajets pour V3-3CH-03 : coordonnées du plan source (avant agrandissement x1.3), puis échelle K et décalage OFF vers plan.png."""
import json
from PIL import Image, ImageDraw
K = 1.3
OFF = (-40, -20)
def o(p): return (p[0]*K+OFF[0], p[1]*K+OFF[1])
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
POLYS = {
 "Entrée": rect(360, 545, 500, 745),
 "Salon": rect(80, 670, 370, 1005),
 "Salle à manger": rect(130, 555, 355, 665),
 "Entrée latérale": rect(85, 262, 215, 495),
 "Salle de bain": rect(225, 268, 320, 385),
 "Chambre 1": rect(160, 48, 335, 255),
 "Chambre 2": rect(520, 68, 720, 262),
 "Salle de bain 2": rect(515, 600, 595, 745),
 "Chambre 3": rect(470, 385, 770, 580),
}
START = (500, 880)
PATHS = {   # waypoints : toujours par les portes / ouvertures
 "Entrée": [START,(480,800),(420,752),(405,690)],
 "Salon": [(405,690),(330,705),(250,780),(225,790)],
 "Salle à manger": [(225,790),(220,700),(240,660),(250,655)],
 "Entrée latérale": [(250,655),(190,600),(180,520),(170,400)],
 "Salle de bain": [(170,400),(240,420),(255,395),(270,330)],
 "Chambre 1": [(270,330),(255,400),(300,440),(390,430),(395,300),(380,262),(320,258),(315,240),(270,200)],
 "Chambre 2": [(270,200),(315,240),(320,258),(380,262),(395,285),(470,280),(545,265),(610,220)],
 "Salle de bain 2": [(610,220),(545,262),(470,275),(420,300),(410,450),(420,560),(470,600),(520,620),(550,660)],
 "Chambre 3": [(550,660),(520,620),(470,600),(420,560),(410,450),(415,378),(520,374),(520,400),(580,470)],
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
