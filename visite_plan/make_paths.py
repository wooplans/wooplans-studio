"""Pièces (polygones) et trajets du point pour V3-003 : coordonnées en pixels de l'image générée (1024), puis décalées (OFF) vers plan.png."""
import json
from PIL import Image, ImageDraw
OFF = (10, 60)
def o(p): return (p[0]+OFF[0], p[1]+OFF[1])
def rect(x0,y0,x1,y1): return [(x0,y0),(x1,y0),(x1,y1),(x0,y1)]
POLYS = {
 "Terrasse 1": rect(392,805,905,915),
 "Séjour": rect(392,440,888,797),
 "Cuisine": rect(668,126,888,420),
 "Terrasse 2": rect(670,36,900,121),
 "Couloir": rect(290,332,656,428),
 "Chambre 3": rect(386,46,650,313),
 "Chambre 2": rect(106,46,368,313),
 "SDB 2": rect(106,331,285,432),
 "Chambre P.": [(106,577),(290,577),(290,440),(368,440),(368,905),(106,905)],
 "SDB 1": rect(106,452,272,562),
}
START = (520, 872)
PATHS = {   # waypoints : toujours par les portes / ouvertures
 "Terrasse 1": [START, (540, 880)],
 "Séjour": [(540,880),(470,860),(437,825),(437,790),(460,750),(560,690),(640,640)],
 "Cuisine": [(640,640),(760,560),(850,470),(855,432),(850,395),(800,330)],
 "Terrasse 2": [(800,330),(740,260),(705,185),(702,128),(730,85),(775,72)],
 "Couloir": [(775,72),(715,105),(702,200),(702,330),(690,392),(655,395),(520,382)],
 "Chambre 3": [(520,382),(430,350),(420,322),(430,260),(450,200)],
 "Chambre 2": [(450,200),(425,290),(400,335),(335,345),(333,320),(320,250),(215,250)],
 "SDB 2": [(215,250),(320,280),(333,325),(330,350),(290,362),(225,372)],
 "Chambre P.": [(225,372),(290,362),(332,372),(335,432),(332,500),(330,580),(300,650),(230,740)],
 "SDB 1": [(230,740),(300,650),(330,580),(331,540),(285,533),(215,500)],
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
    rooms.append({"name":name,"path":[list(o(p)) for p in sm],"poly":[list(o(p)) for p in POLYS[name]]})
json.dump({"start":list(o(START)),"rooms":rooms},open("paths.json","w"),indent=1,ensure_ascii=False)
img=Image.open("plan.png").convert("RGB"); d=ImageDraw.Draw(img,"RGBA")
cols=[(240,138,46),(200,0,0),(0,120,255),(0,160,0),(160,0,200),(0,160,160),(200,120,0),(255,0,120),(90,90,90),(0,0,0)]
for i,r in enumerate(rooms):
    c=cols[i%len(cols)]
    d.polygon([tuple(p) for p in r["poly"]],fill=c+(45,),outline=c+(255,))
    d.line([tuple(p) for p in r["path"]],fill=c+(255,),width=4)
img.save("paths_check.png")
