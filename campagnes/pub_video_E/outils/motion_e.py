"""Pub vidéo E : clips animés (720x1280, 30 i/s)."""
import sys, math, subprocess, random
sys.path.insert(0, '/tmp/claude-0/-home-user/6c90d4e0-3fe0-5e06-8109-0705ee73adcb/scratchpad/scripts')
import motion as M
from motion import F, ease, pop, ctext, rrect, paste_scaled, cover, W, H, FPS, BLACK, BOLD, GOLD, ORANGE, WHITE, TEAL_XDK
from PIL import Image, ImageDraw, ImageFilter
E = '/tmp/claude-0/-home-user/6c90d4e0-3fe0-5e06-8109-0705ee73adcb/scratchpad/pubE/'
V = M.D

def frames(src, start, dur, speed=1.0):
    """images d'une vidéo, recadrées 720x1280"""
    vf = f'setpts=PTS/{speed},scale={W}:-2,crop={W}:{H},fps={FPS}' if speed != 1 else f'scale={W}:-2,crop={W}:{H},fps={FPS}'
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(start), '-i', src, '-vf', vf, '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    n = int(round(dur * FPS)); out = []; last = None
    while len(out) < n:
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        last = Image.frombytes('RGB', (W, H), b); out.append(last)
    p.kill()
    while len(out) < n: out.append(last)
    return out

def write(name, imgs):
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS), '-i', '-',
                          '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', E + 'clips/' + name + '.mp4'], stdin=subprocess.PIPE)
    for im in imgs: p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', name, len(imgs) / FPS)

def zoom(im, z, cx=0.5, cy=0.5):
    if z <= 1.0001: return im
    w, h = int(W / z), int(H / z); x = int((W - w) * cx); y = int((H - h) * cy)
    return im.crop((x, y, x + w, y + h)).resize((W, H), Image.LANCZOS)

def slam(im, txt, t, t0, y, size, fill=WHITE, stroke=ORANGE, sw=8):
    """texte qui « tombe » (grand -> taille normale) avec secousse"""
    k = (t - t0) / 0.22
    if k < 0: return im
    s = 1 + 0.9 * (1 - ease(k)) if k < 1 else 1.0
    lay = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
    w = d.textlength(txt, font=F(BLACK, size))
    d.text(((W - w) / 2, 40), txt, font=F(BLACK, size), fill=fill, stroke_width=sw, stroke_fill=stroke)
    sh = Image.new('RGBA', lay.size, (0, 0, 0, 0)); sh.paste((0, 0, 0, 150), (0, 0), lay.getchannel('A'))
    sh = sh.filter(ImageFilter.GaussianBlur(10))
    base = im.convert('RGBA')
    j = (random.uniform(-6, 6), random.uniform(-6, 6)) if 0 < k < 1.6 else (0, 0)
    for L, off in [(sh, (6, 10)), (lay, (0, 0))]:
        paste_scaled(base, L, W / 2 + j[0] + off[0], y + j[1] + off[1], s)
    return base

def pill(im, txt, y, t, t0, fill=ORANGE, col=WHITE, size=44, x=None):
    k = ease((t - t0) / 0.3)
    if k <= 0: return im
    base = im.convert('RGBA'); d0 = ImageDraw.Draw(base)
    w = d0.textlength(txt, font=F(BLACK, size)) + 64; h = size + 40
    c = Image.new('RGBA', (int(w), int(h)), (0, 0, 0, 0)); d = ImageDraw.Draw(c)
    d.rounded_rectangle((0, 0, w - 1, h - 1), h // 2, fill=fill)
    d.text((32, 16), txt, font=F(BLACK, size), fill=col)
    paste_scaled(base, c, (x or W / 2), y, pop((t - t0) / 0.35))
    return base

def vignette(im, a=110):
    v = Image.new('L', (W, H), 0); d = ImageDraw.Draw(v)
    d.rectangle((0, 0, W, 330), fill=a)
    v = v.filter(ImageFilter.GaussianBlur(80))
    dark = Image.new('RGB', (W, H), (0, 0, 0))
    return Image.composite(dark, im.convert('RGB'), v)

# ---- 1. hook : brouette de billets (0 -> 1.35) ----
def hook1():
    fr = frames(E + 'H1.mp4', 0.25, 1.35)
    out = []
    for i, im in enumerate(fr):
        t = i / FPS
        im = zoom(im, 1.12 - 0.08 * t, 0.5, 0.6)
        im = vignette(im)
        if i < 2: im = Image.blend(im, Image.new('RGB', (W, H), WHITE), 0.6)
        im = slam(im, 'DES MILLIONS', t, 0.05, 200, 88)
        out.append(im)
    write('01_hook1', out)

# ---- 2. terrain vide (1.35 -> 2.6) ----
def hook2():
    fr = frames(V + 'B_terrain.mp4', 0.6, 1.25)
    out = []
    for i, im in enumerate(fr):
        t = i / FPS
        im = vignette(zoom(im, 1.05 + 0.1 * t))
        im = slam(im, 'DES MILLIONS', 9, 0, 200, 88)          # reste affiché, fixe
        im = slam(im, 'POUR VOTRE MAISON…', t, 0.0, 330, 58, fill=GOLD, stroke=(0, 0, 0), sw=5)
        out.append(im)
    write('02_hook2', out)

# ---- 3. présentateur : « ... pas encore un plan qui vous intéresse ? » (2.6 -> 5.85) ----
def hook3():
    fr = frames(E + 'PA2.mp4', 0.15, 3.25)
    out = []
    for i, im in enumerate(fr):
        t = i / FPS
        z = 1.0 + 0.03 * t if t < 1.72 else 1.12 + 0.02 * (t - 1.72)   # coup de zoom sur « plan »
        im = vignette(zoom(im, z, 0.5, 0.2), 90)
        if 1.72 <= t < 1.79: im = Image.blend(im, Image.new('RGB', (W, H), WHITE), 0.35)
        im = slam(im, 'SANS UN PLAN', t, 1.72, 190, 84, fill=WHITE, stroke=(200, 40, 40))
        im = slam(im, 'QUI VOUS PLAÎT ?', t, 1.95, 300, 70, fill=GOLD, stroke=(0, 0, 0), sw=6)
        out.append(im)
    write('03_hook3', out)

# ---- 4. 100 plans (5.85 -> 8.95) ----
def cent():
    R = M.renders_list()
    tiles = [r.resize((300, 188), Image.LANCZOS) for r in R]
    out = []
    dur = 3.1
    for i in range(int(dur * FPS)):
        t = i / FPS
        im = M.base(); d = ImageDraw.Draw(im)
        # mur de rendus qui défile en diagonale
        off = int(t * 140)
        for row in range(7):
            for col in range(4):
                tile = tiles[(row * 4 + col + row) % len(tiles)]
                x = col * 316 - 160 + (row % 2) * 150 - off % 316
                y = row * 204 - 120 + int(t * 40)
                m = Image.new('L', tile.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 299, 187), 22, fill=255)
                im.paste(tile, (x, y), m)
        im = Image.blend(im, M.base(), 0.35)
        d = ImageDraw.Draw(im)
        rrect(d, (60, 430, 660, 860), 48, (7, 46, 45))
        n = int(100 * ease(t / 1.6))
        ctext(d, 450, f'{n}', F(BLACK, 250), GOLD)
        ctext(d, 720, 'PLANS', F(BLACK, 96), WHITE)
        k = ease((t - 1.3) / 0.4)
        if k > 0:
            rrect(d, (110, 900, 610, 990), 45, ORANGE)
            ctext(d, 915, 'VILLAS & DUPLEX', F(BLACK, 52), WHITE)
        out.append(im)
    write('04_cent', out)

# ---- 5. devis (8.95 -> 11.65) ----
def devis():
    fr = frames(V + 'M_devis.mp4', 0.0, 2.7)
    write('05_devis', fr)

# ---- 6. famille (11.65 -> 13.95) ----
def famille():
    fr = frames(V + 'B_famille.mp4', 0.3, 2.3)
    out = [vignette(zoom(im, 1.04 + 0.05 * i / FPS)) for i, im in enumerate(fr)]
    out = [pill(im, 'EN FAMILLE', 200, i / FPS, 0.1, fill=(7, 46, 45), col=GOLD) for i, im in enumerate(out)]
    write('06_famille', out)

# ---- 7. téléphone : choisir selon budget + terrain (13.95 -> 17.55) ----
def phone():
    R = M.renders_list()
    PW, PH = 400, 820
    screen_tiles = [r.resize((PW - 40, 225), Image.LANCZOS) for r in R]
    out = []
    dur = 3.6
    for i in range(int(dur * FPS)):
        t = i / FPS
        im = M.base(); d = ImageDraw.Draw(im)
        ph = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); pd = ImageDraw.Draw(ph)
        pd.rounded_rectangle((0, 0, PW - 1, PH - 1), 56, fill=(20, 20, 22))
        scr = Image.new('RGB', (PW - 40, PH - 60), (245, 246, 244)); sd = ImageDraw.Draw(scr)
        off = int(ease(t / 2.2) * 700)
        for k, tile in enumerate(screen_tiles[:8]):
            y = 20 + k * 250 - off
            if -260 < y < PH:
                scr.paste(tile, (0, y))
                sd.text((14, y + 228 - 2), '', font=F(BOLD, 18))
        # surlignage de la maison choisie
        if t > 2.3:
            sd.rounded_rectangle((4, 20 + 3 * 250 - off - 4, PW - 44, 20 + 3 * 250 - off + 229), 14, outline=ORANGE, width=8)
        ph.paste(scr, (20, 30))
        tilt = 0
        paste_scaled(im, ph, W / 2, 610 + int((1 - ease(t / 0.4)) * 300), 1.0)
        im = pill(im, '✓ VOTRE BUDGET', 140, t, 1.85, fill=(46, 160, 90), size=46)
        im = pill(im, '✓ VOTRE TERRAIN', 1110, t, 2.75, fill=(46, 160, 90), size=46)
        out.append(im)
    write('07_phone', out)

# ---- 8. prix (17.55 -> 19.65) ----
def prix():
    out = [M.prix(i / FPS, 1.5) for i in range(int(1.5 * FPS))]
    write('08_prix', out)

# ---- 9. rappel du hook : brouette de billets vs 1 brouette (19.65 -> 21.65) ----
def callback():
    top = frames(E + 'H1.mp4', 0.9, 2.0)
    bot = frames(V + 'B_brouette.mp4', 0.5, 2.0)
    out = []
    for i in range(len(top)):
        t = i / FPS
        im = Image.new('RGB', (W, H), (7, 46, 45))
        a = top[i].resize((W, H), Image.LANCZOS).crop((0, 330, W, 330 + 630))
        b = bot[i].crop((0, 330, W, 330 + 630))
        k = ease(t / 0.35)
        im.paste(a, (int(-W * (1 - k)), 0)); im.paste(b, (int(W * (1 - k)), 650))
        d = ImageDraw.Draw(im)
        d.rectangle((0, 630, W, 650), fill=GOLD)
        im = pill(im, 'VOTRE MAISON : DES MILLIONS', 70, t, 0.15, fill=(0, 0, 0), col=WHITE, size=38)
        im = pill(im, 'LE CATALOGUE : 39 000 F', 1210, t, 0.6, fill=ORANGE, col=WHITE, size=46)
        out.append(im)
    write('09_callback', out)

# ---- 10. garantie sur présentateur (21.65 -> 25.95) ----
def garantie():
    fr = frames(E + 'PB.mp4', 0.05, 4.3)
    badge = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); b = ImageDraw.Draw(badge)
    for j in range(24):
        a = j * math.pi / 12
        b.polygon([(150 + 148 * math.cos(a), 150 + 148 * math.sin(a)), (150 + 124 * math.cos(a + 0.13), 150 + 124 * math.sin(a + 0.13)),
                   (150 + 124 * math.cos(a - 0.13), 150 + 124 * math.sin(a - 0.13))], fill=GOLD)
    b.ellipse((26, 26, 274, 274), fill=GOLD); b.ellipse((42, 42, 258, 258), outline=TEAL_XDK, width=5)
    for txt, y, sz in [('7', 50, 104), ('JOURS', 160, 38), ('REMBOURSÉ', 208, 22)]:
        w = b.textlength(txt, font=F(BLACK, sz)); b.text((150 - w / 2, y), txt, font=F(BLACK, sz), fill=TEAL_XDK)
    out = []
    for i, im in enumerate(fr):
        t = i / FPS
        im = vignette(zoom(im, 1.06 + 0.02 * t, 0.5, 0.3), 70).convert('RGBA')
        k = (t - 1.9)
        if k > 0:
            paste_scaled(im, badge, 560, 250, pop(k / 0.45) * (1 + 0.03 * math.sin(t * 4)))
        out.append(im)
    write('10_garantie', out)

# ---- 11. appel à l'action (25.95 -> 30.4) ----
def cta():
    fr = frames(E + 'PB.mp4', 4.35, 4.45)
    out = []
    for i, im in enumerate(fr):
        t = i / FPS
        im = vignette(zoom(im, 1.06 + 0.015 * t, 0.5, 0.3), 80).convert('RGBA')
        im = pill(im, 'CATALOGUE PREMIUM · 39 000 FCFA', 130, t, 0.1, fill=(7, 46, 45), col=GOLD, size=36)
        im = pill(im, 'wooplans.com', 215, t, 0.4, fill=WHITE, col=TEAL_XDK, size=36)
        if t > 1.0:  # flèche qui rebondit vers le bouton
            d = ImageDraw.Draw(im); y = 1150 + int(18 * abs(math.sin((t - 1) * 5)))
            d.polygon([(W / 2 - 50, y - 40), (W / 2 + 50, y - 40), (W / 2, y + 20)], fill=ORANGE)
        out.append(im)
    write('11_cta', out)

def compare():
    """brouette et catalogue côte à côte, 39 000 FCFA en grand (19.07 -> 21.67)"""
    M.catalogue(0, 1); cov = M.COVER
    bro = frames(V + 'B_brouette.mp4', 0.3, 2.6)
    out = []
    CW, CH = 320, 470
    for i, fr in enumerate(bro):
        t = i / FPS
        im = M.base(); d = ImageDraw.Draw(im)
        ctext(d, 120, "LE PRIX D'UNE BROUETTE", F(BLACK, 54), WHITE)
        ctext(d, 190, 'pour choisir votre maison', F(BOLD, 34), (220, 235, 233))
        b = cover_img(fr, CW, CH, 0.45)
        c = Image.new('RGB', (CW, CH), (236, 240, 238)); cs = cov.copy(); cs.thumbnail((CW - 30, CH - 20))
        c.paste(cs, ((CW - cs.width) // 2, (CH - cs.height) // 2), cs)
        for img, x, k in [(b, 25, ease(t / 0.35)), (c, 375, ease((t - 0.2) / 0.35))]:
            if k <= 0: continue
            m = Image.new('L', (CW, CH), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, CW - 1, CH - 1), 28, fill=255)
            im.paste(img, (x, 280 + int((1 - k) * 90)), m)
        d = ImageDraw.Draw(im)
        for txt, cx in [('1 brouette', 185), ('le catalogue', 535)]:
            w = d.textlength(txt, font=F(BLACK, 38)); d.text((cx - w / 2, 770), txt, font=F(BLACK, 38), fill=GOLD)
        k = (t - 0.35) / 0.3
        if k > 0:
            eq = Image.new('RGBA', (110, 110), (0, 0, 0, 0)); e = ImageDraw.Draw(eq)
            e.ellipse((0, 0, 109, 109), fill=GOLD); w = e.textlength('=', font=F(BLACK, 90)); e.text((55 - w / 2, -4), '=', font=F(BLACK, 90), fill=TEAL_XDK)
            paste_scaled(im, eq, W / 2, 515, pop(k))
        k = (t - 0.6) / 0.4
        if k > 0:
            pr = Image.new('RGBA', (640, 190), (0, 0, 0, 0)); pd = ImageDraw.Draw(pr)
            pd.rounded_rectangle((0, 0, 639, 189), 40, fill=ORANGE)
            w = pd.textlength('39 000 FCFA', font=F(BLACK, 96)); pd.text((320 - w / 2, 38), '39 000 FCFA', font=F(BLACK, 96), fill=WHITE)
            paste_scaled(im, pr, W / 2, 940, pop(k) * (1 + 0.015 * math.sin(t * 6)))
            d = ImageDraw.Draw(im); ctext(d, 1060, '(une brouette ≈ 35 000 FCFA)', F(BOLD, 30), (200, 220, 218))
        out.append(im)
    write('09_callback', out)

def cover_img(im, w, h, cy=0.5):
    s = max(w / im.width, h / im.height); r = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = (r.width - w) // 2; y = int((r.height - h) * cy); return r.crop((x, y, x + w, y + h))

if __name__ == '__main__':
    random.seed(4)
    for n in sys.argv[1:]: globals()[n]()
