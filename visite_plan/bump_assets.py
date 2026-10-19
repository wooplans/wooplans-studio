from PIL import Image, ImageDraw, ImageFont, ImageChops
G=(15,91,89); O=(240,138,46)
F="/usr/share/fonts/truetype/google-fonts/Poppins-Bold.ttf"
logo=Image.open("../out/logo_white.png").convert("RGBA")
def lg(h): return logo.resize((round(logo.width*h/logo.height),h),Image.LANCZOS)
# bande basse 1080x190
band=Image.new("RGBA",(1080,190),G+(255,)); d=ImageDraw.Draw(band)
d.rectangle([0,0,1080,6],fill=O+(255,))
L=lg(118); f=ImageFont.truetype(F,76); txt="wooplans.com"; tw=d.textlength(txt,font=f)
gap=36; tot=L.width+gap+tw; x0=(1080-tot)/2; cy=(190+6)/2
band.alpha_composite(L,(round(x0),round(cy-L.height/2)))
d.text((x0+L.width+gap,cy+2),txt,font=f,fill="white",anchor="lm")
band.save("band_bottom.png")
# badge URL (zone sûre, coin de la façade)
def pill(w,h,h_logo,fs,alpha):
    im=Image.new("RGBA",(w,h),(0,0,0,0)); d=ImageDraw.Draw(im)
    d.rounded_rectangle([0,0,w-1,h-1],radius=h//2,fill=G+(alpha,))
    L=lg(h_logo); im.alpha_composite(L,(h//3,(h-L.height)//2))
    f=ImageFont.truetype(F,fs)
    d.text((h//3+L.width+14,h/2+1),"wooplans.com",font=f,fill="white",anchor="lm")
    return im
pill(420,76,50,36,225).save("badge_url.png")
pill(310,56,38,25,125).save("wm_logo.png")
# filigrane en mosaïque, très discret
W,H=1080,1920
tile=Image.new("RGBA",(W,H),(0,0,0,0))
ic=lg(70); a=ic.split()[-1].point(lambda v:int(v*0.075))
col=Image.new("RGBA",ic.size,(150,170,170,255)); col.putalpha(a)
big=Image.new("RGBA",(W*2,H*2),(0,0,0,0))
sx,sy=300,260
for r,y in enumerate(range(0,H*2,sy)):
    for x in range(-sx, W*2, sx):
        big.alpha_composite(col,(x+(sx//2 if r%2 else 0), y)) if 0<=x+(sx//2 if r%2 else 0)<W*2-ic.width else None
big=big.rotate(-20,resample=Image.BICUBIC)
tile=big.crop((W//2,H//2,W//2+W,H//2+H)); tile.save("wm_tile.png")
print("ok")
