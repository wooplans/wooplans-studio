"""Pub vidéo E en anglais (Kenya / Ghana) : même méthode que la vidéo E française.
Clips IA Runware (p-video@2), présentateur animé par sa voix, montage image par image (720x1280, 30 i/s),
mots-clés qui tombent, coups de zoom, compteur 100 PLANS, écran partagé « millions / catalogue », badge garantie.
Usage : python3 motion_en.py KE|GH
"""
import sys, math, random, subprocess, glob, json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

CC = sys.argv[1]
D = '/tmp/claude-0/-home-user/5c2e67f5-e463-50b2-bad9-952a748cbb7a/scratchpad/pubE_en/'
OUT = D + f'clips_{CC}/'
subprocess.run(['mkdir', '-p', OUT])
W, H, FPS = 720, 1280, 30
TEAL, TEAL_XDK, ORANGE, GOLD, WHITE = (15, 91, 89), (7, 46, 45), (240, 138, 46), (231, 195, 108), (255, 255, 255)
BLACK = '/usr/share/fonts/opentype/inter/Inter-Black.otf'
BOLD = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
_f = {}
def F(path, size):
    k = (path, size)
    if k not in _f: _f[k] = ImageFont.truetype(path, size)
    return _f[k]

C = {'KE': dict(price='KES 8,892', pay='PAY WITH M-PESA', H1='H1_KE.mp4', PA='PA_KE.mp4', PB='PB_KE.mp4',
                cuts=[0, 4.04, 6.4, 9.77, 11.03, 13.53, 16.6], a2=19.41, pb_split=3.92, tcat=2.0),
     'GH': dict(price='GHS 796', pay='PAY WITH MTN MOMO', H1='H1_GH.mp4', PA='PA_GH.mp4', PB='PB_GH.mp4',
                cuts=[0, 4.26, 6.48, 9.86, 11.23, 13.6, 16.65], a2=18.83, pb_split=4.0, tcat=2.14)}[CC]

def ease(k):
    k = max(0.0, min(1.0, k)); return 1 - (1 - k) ** 3
def pop(k):
    k = max(0.0, min(1.0, k)); return 1 + 0.25 * math.sin(k * math.pi) * (1 - k) if k < 1 else 1.0

def frames(src, start, dur):
    vf = f'scale={W}:-2,crop={W}:{H},fps={FPS}'
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
                          '-c:v', 'libx264', '-crf', '17', '-preset', 'medium', '-pix_fmt', 'yuv420p', OUT + name + '.mp4'], stdin=subprocess.PIPE)
    for im in imgs: p.stdin.write(im.convert('RGB').tobytes())
    p.stdin.close(); p.wait(); print('ok', CC, name, round(len(imgs) / FPS, 2))

def zoom(im, z, cx=0.5, cy=0.5):
    if z <= 1.0001: return im
    w, h = int(W / z), int(H / z); x = int((W - w) * cx); y = int((H - h) * cy)
    return im.crop((x, y, x + w, y + h)).resize((W, H), Image.LANCZOS)

def paste_scaled(base, lay, cx, cy, s):
    if s != 1:
        lay = lay.resize((max(1, int(lay.width * s)), max(1, int(lay.height * s))), Image.LANCZOS)
    base.alpha_composite(lay, (int(cx - lay.width / 2), int(cy - lay.height / 2)))

def slam(im, txt, t, t0, y, size, fill=WHITE, stroke=ORANGE, sw=8):
    """texte qui « tombe » (grand -> taille normale) avec secousse"""
    k = (t - t0) / 0.22
    if k < 0: return im
    s = 1 + 0.9 * (1 - ease(k)) if k < 1 else 1.0
    lay = Image.new('RGBA', (W, size + 120), (0, 0, 0, 0)); d = ImageDraw.Draw(lay)
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
    d.text((32, 14), txt, font=F(BLACK, size), fill=col)
    paste_scaled(base, c, (x or W / 2), y, pop((t - t0) / 0.35))
    return base

def vignette(im, a=110):
    v = Image.new('L', (W, H), 0); d = ImageDraw.Draw(v)
    d.rectangle((0, 0, W, 330), fill=a)
    v = v.filter(ImageFilter.GaussianBlur(80))
    return Image.composite(Image.new('RGB', (W, H), (0, 0, 0)), im.convert('RGB'), v)

def base_bg():
    im = Image.new('RGB', (W, H), TEAL); d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H; d.line([(0, y), (W, y)], fill=tuple(int(TEAL[i] * (1 - k) + TEAL_XDK[i] * k) for i in range(3)))
    return im

def ctext(d, y, txt, font, fill):
    w = d.textlength(txt, font=font); d.text(((W - w) / 2, y), txt, font=font, fill=fill)

def renders():
    out = []
    for f in sorted(glob.glob(D + 'renders/*.webp')):
        im = Image.open(f).convert('RGB'); im = im.crop((0, 0, im.width, int(im.height * 0.86)))  # retire le badge « Visitez wooplans.com »
        out.append(im)
    return out
R = renders()

# ---- 1. hook : brouette de billets ----
def hook1():
    fr = frames(D + C['H1'], 0.25, 1.4); out = []
    for i, im in enumerate(fr):
        t = i / FPS
        im = vignette(zoom(im, 1.12 - 0.08 * t, 0.5, 0.6))
        if i < 2: im = Image.blend(im, Image.new('RGB', (W, H), WHITE), 0.6)
        out.append(slam(im, 'MILLIONS', t, 0.05, 200, 110))
    write('01_hook1', out)

# ---- 2. terrain vide ----
def hook2():
    fr = frames(D + 'B_terrain.mp4', 0.6, 1.45); out = []
    for i, im in enumerate(fr):
        t = i / FPS
        im = vignette(zoom(im, 1.05 + 0.1 * t))
        im = slam(im, 'MILLIONS', 9, 0, 200, 110)
        out.append(slam(im, 'FOR YOUR HOUSE…', t, 0.0, 340, 58, fill=GOLD, stroke=(0, 0, 0), sw=5))
    write('02_hook2', out)

# ---- 3. présentateur : « …and you still don't have a plan you like? » ----
def hook3():
    fr = frames(D + C['PA'], 0.0, 3.0); out = []
    for i, im in enumerate(fr):
        t = i / FPS
        z = 1.0 + 0.03 * t if t < 1.5 else 1.12 + 0.02 * (t - 1.5)   # coup de zoom sur « plan »
        im = vignette(zoom(im, z, 0.5, 0.2), 90)
        if 1.5 <= t < 1.57: im = Image.blend(im, Image.new('RGB', (W, H), WHITE), 0.35)
        im = slam(im, 'NO PLAN', t, 1.5, 190, 96, fill=WHITE, stroke=(200, 40, 40))
        out.append(slam(im, 'YOU LIKE?', t, 1.72, 310, 76, fill=GOLD, stroke=(0, 0, 0), sw=6))
    write('03_hook3', out)

# ---- 4. 100 plans ----
def cent(dur):
    tiles = [r.resize((300, int(300 * r.height / r.width)), Image.LANCZOS).crop((0, 0, 300, 188)) for r in R]
    m = Image.new('L', (300, 188), 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 299, 187), 22, fill=255)
    out = []
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = base_bg(); off = int(t * 140)
        for row in range(7):
            for col in range(4):
                tile = tiles[(row * 4 + col + row) % len(tiles)]
                im.paste(tile, (col * 316 - 160 + (row % 2) * 150 - off % 316, row * 204 - 120 + int(t * 40)), m)
        im = Image.blend(im, base_bg(), 0.35); d = ImageDraw.Draw(im)
        d.rounded_rectangle((60, 430, 660, 860), 48, fill=TEAL_XDK)
        ctext(d, 450, f'{int(100 * ease(t / 1.6))}', F(BLACK, 250), GOLD)
        ctext(d, 720, 'HOUSE PLANS', F(BLACK, 80), WHITE)
        out.append(im)
    write('04_cent', out)

# ---- 5. bungalows et two-story ----
def types(dur):
    a, b = R[0], R[1]
    out = []
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = base_bg()
        for k, (r, y, lab, t0) in enumerate([(a, 330, 'BUNGALOWS', 0.0), (b, 860, 'TWO-STORY HOUSES', 0.5)]):
            kk = ease((t - t0) / 0.35)
            if kk <= 0: continue
            tile = r.resize((660, int(660 * r.height / r.width)), Image.LANCZOS).crop((0, 0, 660, 400))
            z = 1 + 0.05 * t
            tile = tile.resize((int(660 * z), int(400 * z)), Image.LANCZOS).crop((0, 0, 660, 400))
            msk = Image.new('L', (660, 400), 0); ImageDraw.Draw(msk).rounded_rectangle((0, 0, 659, 399), 30, fill=255)
            x = int(30 + (1 - kk) * (W if k == 0 else -W))
            im.paste(tile, (x, y - 200), msk)
            im = pill(im, lab, y + 170, t, t0 + 0.2, fill=ORANGE, size=40)
        out.append(im)
    write('05_types', out)

# ---- 6. calculateur ----
def calc(dur):
    cap = Image.open(D + f'../prem-calc-{CC}.png').convert('RGB')
    cw = 600; cap = cap.resize((cw, int(cap.height * cw / cap.width)), Image.LANCZOS)
    out = []
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = base_bg().convert('RGBA')
        k = ease(t / 0.4); y0 = 290 + int((1 - k) * 600)
        view = cap.crop((0, int(min(cap.height - 820, max(0, (t - 0.8) * 90))), cw, int(min(cap.height - 820, max(0, (t - 0.8) * 90))) + 820))
        frame = Image.new('RGBA', (cw + 24, 844), (20, 20, 22, 255)); m = Image.new('L', frame.size, 0)
        ImageDraw.Draw(m).rounded_rectangle((0, 0, frame.width - 1, frame.height - 1), 40, fill=255)
        frame.paste(view, (12, 12))
        im.paste(frame, ((W - frame.width) // 2, y0), m)
        im = slam(im, 'COST CALCULATOR', t, 0.3, 110, 64, fill=WHITE, stroke=ORANGE, sw=6)
        out.append(im)
    write('06_calc', out)

# ---- 7. famille ----
def famille(dur):
    fr = frames(D + 'B_famille.mp4', 0.3, dur)
    out = [vignette(zoom(im, 1.04 + 0.05 * i / FPS)) for i, im in enumerate(fr)]
    out = [pill(im, 'WITH YOUR FAMILY', 200, i / FPS, 0.1, fill=TEAL_XDK, col=GOLD) for i, im in enumerate(out)]
    write('07_famille', out)

# ---- 8. téléphone : budget + terrain ----
def phone(dur):
    PW, PH = 400, 820
    tiles = [r.resize((PW - 40, int((PW - 40) * r.height / r.width)), Image.LANCZOS).crop((0, 0, PW - 40, 225)) for r in R]
    out = []
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = base_bg().convert('RGBA')
        ph = Image.new('RGBA', (PW, PH), (0, 0, 0, 0)); pd = ImageDraw.Draw(ph)
        pd.rounded_rectangle((0, 0, PW - 1, PH - 1), 56, fill=(20, 20, 22))
        scr = Image.new('RGB', (PW - 40, PH - 60), (245, 246, 244)); sd = ImageDraw.Draw(scr)
        off = int(ease(t / (dur * 0.6)) * 700)
        for k, tile in enumerate(tiles[:8]):
            y = 20 + k * 250 - off
            if -260 < y < PH: scr.paste(tile, (0, y))
        if t > dur * 0.62:
            sd.rounded_rectangle((4, 20 + 3 * 250 - off - 4, PW - 44, 20 + 3 * 250 - off + 229), 14, outline=ORANGE, width=8)
        ph.paste(scr, (20, 30))
        paste_scaled(im, ph, W / 2, 640 + int((1 - ease(t / 0.4)) * 300), 1.0)
        im = pill(im, '✓ YOUR BUDGET', 150, t, dur * 0.25, fill=(46, 160, 90), size=46)
        im = pill(im, '✓ YOUR PLOT', 1130, t, dur * 0.6, fill=(46, 160, 90), size=46)
        out.append(im)
    write('08_phone', out)

# ---- 9. rappel du hook : des millions contre le catalogue ----
def callback(dur, t_cat):
    top = frames(D + C['H1'], 0.9, dur)
    cover = R[0].resize((W, int(W * R[0].height / R[0].width)), Image.LANCZOS)
    out = []
    for i in range(len(top)):
        t = i / FPS
        im = Image.new('RGB', (W, H), TEAL_XDK)
        a = top[i].crop((0, 330, W, 330 + 630))
        k = ease(t / 0.35); im.paste(a, (int(-W * (1 - k)), 0))
        kb = ease((t - t_cat) / 0.35)
        if kb > 0:
            b = Image.new('RGB', (W, 630), TEAL)
            b.paste(cover.crop((0, 0, W, min(cover.height, 630))), (0, 0))
            im.paste(b, (int(W * (1 - kb)), 650))
        d = ImageDraw.Draw(im); d.rectangle((0, 630, W, 650), fill=GOLD)
        im = pill(im, 'YOUR HOUSE: MILLIONS', 70, t, 0.15, fill=(0, 0, 0), col=WHITE, size=40)
        im = pill(im, f'THE CATALOGUE: {C["price"]}', 1200, t, t_cat + 0.2, fill=ORANGE, col=WHITE, size=42)
        out.append(im)
    write('09_callback', out)

# ---- 10. prix ----
def prix(dur):
    out = []
    for i in range(int(round(dur * FPS))):
        t = i / FPS
        im = base_bg().convert('RGBA'); d = ImageDraw.Draw(im)
        ctext(d, 330, 'CURRENT PRICE', F(BOLD, 44), GOLD)
        lay = Image.new('RGBA', (W, 220), (0, 0, 0, 0)); ld = ImageDraw.Draw(lay)
        f = F(BLACK, 120); w = ld.textlength(C['price'], font=f)
        ld.rounded_rectangle(((W - w) / 2 - 36, 20, (W + w) / 2 + 36, 200), 40, fill=ORANGE)
        ld.text(((W - w) / 2, 34), C['price'], font=f, fill=WHITE)
        paste_scaled(im, lay, W / 2, 520, pop(t / 0.4) if t < 0.4 else 1.0)
        im = pill(im, '100 HOUSE PLANS · LIFETIME ACCESS', 700, t, 0.4, fill=TEAL_XDK, col=WHITE, size=32)
        im = pill(im, C['pay'], 820, t, 0.7, fill=WHITE, col=TEAL_XDK, size=40)
        out.append(im)
    write('10_prix', out)

# ---- 11. garantie (présentateur) ----
def garantie():
    fr = frames(D + C['PB'], 0.0, C['pb_split'] + 0.1)
    badge = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); b = ImageDraw.Draw(badge)
    for j in range(24):
        a = j * math.pi / 12
        b.polygon([(150 + 148 * math.cos(a), 150 + 148 * math.sin(a)), (150 + 124 * math.cos(a + 0.13), 150 + 124 * math.sin(a + 0.13)),
                   (150 + 124 * math.cos(a - 0.13), 150 + 124 * math.sin(a - 0.13))], fill=GOLD)
    b.ellipse((26, 26, 274, 274), fill=GOLD); b.ellipse((42, 42, 258, 258), outline=TEAL_XDK, width=5)
    for txt, y, sz in [('7', 46, 104), ('DAYS', 158, 40), ('MONEY-BACK', 208, 26)]:
        w = b.textlength(txt, font=F(BLACK, sz)); b.text((150 - w / 2, y), txt, font=F(BLACK, sz), fill=TEAL_XDK)
    out = []
    for i, im in enumerate(fr):
        t = i / FPS
        im = vignette(zoom(im, 1.06 + 0.02 * t, 0.5, 0.3), 70).convert('RGBA')
        if t > 1.6: paste_scaled(im, badge, 560, 250, pop((t - 1.6) / 0.45) * (1 + 0.03 * math.sin(t * 4)))
        out.append(im)
    write('11_garantie', out)

# ---- 12. appel à l'action (présentateur) ----
def cta():
    s = C['pb_split'] + 0.1
    fr = frames(D + C['PB'], s, 7.04 - s + 0.5)
    out = []
    for i, im in enumerate(fr):
        t = i / FPS
        im = vignette(zoom(im, 1.06 + 0.015 * t, 0.5, 0.3), 80).convert('RGBA')
        im = pill(im, f'PREMIUM CATALOGUE · {C["price"]}', 130, t, 0.1, fill=TEAL_XDK, col=GOLD, size=34)
        im = pill(im, 'wooplans.com', 215, t, 0.4, fill=WHITE, col=TEAL_XDK, size=36)
        if t > 0.8:
            d = ImageDraw.Draw(im); y = 1150 + int(18 * abs(math.sin((t - 0.8) * 5)))
            d.polygon([(W / 2 - 50, y - 40), (W / 2 + 50, y - 40), (W / 2, y + 20)], fill=ORANGE)
        out.append(im)
    write('12_cta', out)

if __name__ == '__main__':
    random.seed(4)
    c = C['cuts']; a2 = C['a2']
    hook1(); hook2(); hook3()
    cent(c[1] - c[0]); types(c[2] - c[1]); calc(c[3] - c[2]); famille(c[4] - c[3]); phone(c[5] - c[4])
    callback(c[6] - c[5], C['tcat']); prix(a2 - c[6] + 0.3)
    garantie(); cta()
