"""Animations de la VSL courte (720x1280, 30 i/s). Usage : python motion.py <nom> [<nom> ...]"""
import subprocess, sys, math, os
from PIL import Image, ImageDraw, ImageFont, ImageFilter

W, H, FPS = 720, 1280, 30
D = '/tmp/claude-0/-home-user/6c90d4e0-3fe0-5e06-8109-0705ee73adcb/scratchpad/vsl/'
A = D + 'assets/'
BLACK = '/usr/share/fonts/opentype/inter/InterDisplay-Black.otf'
BOLD = '/usr/share/fonts/opentype/inter/Inter-Bold.otf'
XB = '/usr/share/fonts/opentype/inter/Inter-ExtraBold.otf'
MED = '/usr/share/fonts/opentype/inter/Inter-Medium.otf'
TEAL, TEAL_DK, TEAL_XDK = (15, 91, 89), (10, 63, 62), (7, 46, 45)
GOLD, ORANGE, WHITE, RED = (231, 195, 108), (240, 138, 46), (255, 255, 255), (199, 91, 58)
_fc = {}


def F(path, size):
    k = (path, size)
    if k not in _fc:
        _fc[k] = ImageFont.truetype(path, size)
    return _fc[k]


def ease(x):
    x = max(0.0, min(1.0, x))
    return 1 - (1 - x) ** 3


def pop(x):  # léger dépassement
    x = max(0.0, min(1.0, x))
    return 1 + 2.2 * (x - 1) ** 3 + 1.2 * (x - 1) ** 2


def bg(top=TEAL, bot=TEAL_XDK):
    im = Image.new('RGB', (W, H))
    d = ImageDraw.Draw(im)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=tuple(int(top[i] * (1 - k) + bot[i] * k) for i in range(3)))
    return im


BG = None


def base():
    global BG
    if BG is None:
        BG = bg()
    return BG.copy()


def cover(path, w=W, h=H, zoom=1.0, cx=0.5, cy=0.5):
    im = Image.open(path).convert('RGB')
    s = max(w / im.width, h / im.height) * zoom
    im = im.resize((int(im.width * s) + 1, int(im.height * s) + 1), Image.LANCZOS)
    x = int((im.width - w) * cx); y = int((im.height - h) * cy)
    return im.crop((x, y, x + w, y + h))


def ctext(d, y, txt, font, fill=WHITE, stroke=0, sfill=(0, 0, 0)):
    w = d.textlength(txt, font=font)
    d.text(((W - w) / 2, y), txt, font=font, fill=fill, stroke_width=stroke, stroke_fill=sfill)


def rrect(d, box, r, fill, outline=None, width=0):
    d.rounded_rectangle(box, r, fill=fill, outline=outline, width=width)


def paste_scaled(im, sub, cx, cy, s, alpha=1.0):
    if s <= 0.01 or alpha <= 0:
        return
    sw, sh = max(1, int(sub.width * s)), max(1, int(sub.height * s))
    t = sub.resize((sw, sh), Image.LANCZOS).convert('RGBA')
    if alpha < 1:
        a = t.getchannel('A').point(lambda v: int(v * alpha))
        t.putalpha(a)
    im.paste(t, (int(cx - sw / 2), int(cy - sh / 2)), t)


def card(w, h, fill=WHITE, r=36):
    c = Image.new('RGBA', (w, h), (0, 0, 0, 0))
    ImageDraw.Draw(c).rounded_rectangle((0, 0, w - 1, h - 1), r, fill=fill)
    return c


def render(name, dur, frame_fn):
    out = D + f'M_{name}.mp4'
    p = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                          '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '18', '-preset', 'medium',
                          '-pix_fmt', 'yuv420p', out], stdin=subprocess.PIPE)
    n = int(round(dur * FPS))
    for i in range(n):
        p.stdin.write(frame_fn(i / FPS, dur).convert('RGB').tobytes())
    p.stdin.close(); p.wait()
    print('ok', out, dur)


# ---------- clips ----------

def budget(t, dur):  # « un budget qui explose »
    im = base(); d = ImageDraw.Draw(im)
    ctext(d, 250, 'BUDGET', F(BLACK, 110), GOLD)
    k = ease(t / (dur * 0.85))
    # barres qui montent
    for i in range(5):
        h = 80 + i * 90 * k + (i == 4) * 120 * k
        x = 130 + i * 98
        col = ORANGE if i < 4 else RED
        rrect(d, (x, 900 - h, x + 70, 900), 10, col)
    # flèche
    x0, y0, x1, y1 = 120, 860, 120 + 480 * k, 860 - 520 * k
    d.line([(x0, y0), (x1, y1)], fill=RED, width=16)
    if k > 0.1:
        d.polygon([(x1 + 18, y1 - 18), (x1 - 40, y1 - 6), (x1 + 6, y1 + 40)], fill=RED)
    ctext(d, 940, 'QUI EXPLOSE', F(BLACK, 90), WHITE)
    return im


def propositions(t, dur):
    im = base(); d = ImageDraw.Draw(im)
    ctext(d, 170, 'CHEZ L\'ARCHITECTE', F(BLACK, 58), GOLD)
    for i in range(3):
        k = ease((t - 0.25 - i * 0.9) / 0.4)
        if k <= 0:
            continue
        y = 330 + i * 190
        x = int(60 + (1 - k) * 600)
        rrect(d, (x, y, x + 600, y + 150), 28, WHITE)
        d.text((x + 34, y + 30), f'Proposition {i + 1}', font=F(XB, 44), fill=TEAL_XDK)
        d.text((x + 34, y + 88), 'à payer', font=F(MED, 34), fill=(90, 90, 90))
        tag = 'PAYÉE'
        tw = d.textlength(tag, font=F(BLACK, 38))
        rrect(d, (x + 560 - tw - 30, y + 45, x + 560, y + 105), 14, RED)
        d.text((x + 560 - tw - 15, y + 50), tag, font=F(BLACK, 38), fill=WHITE)
    k = ease((t - 3.2) / 0.5)
    if k > 0:
        paste_scaled(im, Image.new('RGBA', (1, 1)), 0, 0, 0)
        ctext(d, 940, 'Et si aucune', F(BLACK, 64), WHITE if k > 0.5 else TEAL)
        ctext(d, 1010, 'ne vous plaît ?', F(BLACK, 64), GOLD if k > 0.5 else TEAL)
    return im


COVER = None


def catalogue(t, dur):  # « C'est pour ça que nous avons créé le Catalogue Premium WooPlans »
    global COVER
    if COVER is None:
        COVER = Image.open('/tmp/claude-0/-home-user/6c90d4e0-3fe0-5e06-8109-0705ee73adcb/scratchpad/old/couv100.png').convert('RGBA')
        COVER = COVER.resize((520, int(COVER.height * 520 / COVER.width)), Image.LANCZOS)
    im = base(); d = ImageDraw.Draw(im)
    s = 0.6 + 0.4 * pop(t / 0.7) + 0.04 * t
    paste_scaled(im, COVER, W / 2, 560, s * 0.95)
    ctext(d, 1080 - 20, 'CATALOGUE PREMIUM', F(BLACK, 62), GOLD)
    return im


RENDERS = None


def renders_list():
    global RENDERS
    if RENDERS is None:
        fs = ['d5012_r0.webp', 'render-v4-036.webp', 'R2.png', 'render-v3-017.webp', 'd5012_r1.webp', 'render-d4-026.webp',
              'render-v4-005.webp', 'R0.png', 'render-d4-034.webp', 'd5012_r2.webp', 'render-v4-032.webp', 'R4.png', 'd5012_r3.webp']
        RENDERS = [cover(A + f, 640, 400) for f in fs]
    return RENDERS


def cent(t, dur):  # compteur 0 -> 100 + défilé de rendus
    im = base(); d = ImageDraw.Draw(im)
    R = renders_list()
    i = int(t / 0.28) % len(R)
    r = R[i]
    m = Image.new('L', r.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, r.width - 1, r.height - 1), 30, fill=255)
    im.paste(r, (40, 170), m)
    n = int(100 * ease(t / (dur * 0.8)))
    ctext(d, 610, f'{n}', F(BLACK, 230), GOLD)
    ctext(d, 860, 'MODÈLES', F(BLACK, 80), WHITE)
    ctext(d, 960, 'villas et duplex · 3 à 5 chambres', F(BOLD, 36), (220, 235, 233))
    return im


PLAN = None


def plan(t, dur):
    global PLAN
    if PLAN is None:
        PLAN = Image.open(A + 'plan_d5012_rdc.jpg').convert('RGB')
        # recadrer sur le dessin (sans bandeau ni coordonnées)
        PLAN = PLAN.crop((520, 40, 1220, 830))
    im = base(); d = ImageDraw.Draw(im)
    z = 1.0 + 0.35 * ease(t / dur)
    w0 = int(640 * z); h0 = int(PLAN.height * w0 / PLAN.width)
    p = PLAN.resize((w0, h0), Image.LANCZOS)
    cx = int((w0 - 640) * 0.45); cy = int((h0 - 720) * 0.4) if h0 > 720 else 0
    p = p.crop((cx, cy, cx + 640, cy + min(720, h0)))
    pc = Image.new('RGB', (660, p.height + 20), WHITE); pc.paste(p, (10, 10))
    k = ease(t / 0.5)
    im.paste(pc, (30, int(160 + (1 - k) * 60)))
    ctext(d, 940, 'PLAN DE L\'INTÉRIEUR', F(BLACK, 56), GOLD)
    ctext(d, 1010, 'avec toutes les dimensions', F(BOLD, 38), WHITE)
    return im


LOTS = [('Fondation', 4321500), ('Élévation RDC', 3184300), ('Dalle', 6141100), ('Élévation étage', 3639200),
        ('Charpente et toiture', 5458800), ('Crépissage et antivols', 6671800), ('Portes et fenêtres', 5003900),
        ('Plomberie et électricité', 4169900), ('Plafond et peinture', 5837800), ('Carrelage', 6115700)]
TOTAL = 50544000


def fcfa(v):
    return f'{v:,}'.replace(',', ' ') + ' FCFA'


def devis(t, dur):
    im = base(); d = ImageDraw.Draw(im)
    ctext(d, 110, 'DEVIS POSTE PAR POSTE', F(BLACK, 52), GOLD)
    ctext(d, 180, 'Exemple réel : duplex D5-012', F(BOLD, 32), (220, 235, 233))
    rrect(d, (40, 250, 680, 1000), 30, WHITE)
    step = (dur * 0.75) / len(LOTS)
    for i, (lab, v) in enumerate(LOTS):
        k = ease((t - 0.2 - i * step) / 0.3)
        if k <= 0:
            continue
        y = 280 + i * 62
        col = tuple(int(255 * (1 - k) + c * k) for c in TEAL_XDK)
        d.text((70, y), lab, font=F(BOLD, 30), fill=col)
        s = fcfa(v); w = d.textlength(s, font=F(XB, 30))
        d.text((650 - w, y), s, font=F(XB, 30), fill=col)
        d.line([(70, y + 50), (650, y + 50)], fill=(230, 233, 236), width=2)
    k = ease((t - dur * 0.82) / 0.4)
    if k > 0:
        rrect(d, (40, 1010 - int(20 * (1 - k)), 680, 1110), 24, ORANGE)
        s = 'TOTAL  ' + fcfa(TOTAL)
        ctext(d, 1035, s, F(BLACK, 42), WHITE)
    return im


def terrain(t, dur):  # taille de terrain + check
    im = base(); d = ImageDraw.Draw(im)
    ctext(d, 130, 'TERRAIN NÉCESSAIRE', F(BLACK, 58), GOLD)
    k = ease(t / 1.0)
    # terrain 17 x 20 m (D5-012), maison 14 x 13 m
    sc = 26
    tw, th = 17 * sc, 20 * sc
    x0, y0 = (W - tw) / 2, 260
    d.rectangle((x0, y0, x0 + tw * k, y0 + th * k), fill=(196, 120, 72))
    d.rectangle((x0, y0, x0 + tw, y0 + th), outline=WHITE, width=4)
    k2 = ease((t - 0.9) / 0.6)
    if k2 > 0:
        hw, hh = 14 * sc * k2, 13 * sc * k2
        hx, hy = x0 + (tw - 14 * sc) / 2, y0 + 70
        d.rectangle((hx, hy, hx + hw, hy + hh), fill=(240, 240, 235), outline=TEAL_XDK, width=4)
        if k2 > 0.95:
            d.text((hx + 120, hy + hh / 2 - 26), 'MAISON', font=F(BLACK, 46), fill=TEAL_XDK)
    d.text((x0 + tw / 2 - 40, y0 - 50), '17 m', font=F(XB, 36), fill=WHITE)
    d.text((x0 + tw + 14, y0 + th / 2 - 20), '20 m', font=F(XB, 36), fill=WHITE)
    k3 = ease((t - 2.6) / 0.5)
    if k3 > 0:
        for j, lab in enumerate(['SUR VOTRE TERRAIN', 'DANS VOTRE BUDGET']):
            kk = ease((t - 2.6 - j * 1.4) / 0.4)
            if kk <= 0:
                continue
            y = 830 + j * 95
            rrect(d, (90, y, 630, y + 78), 20, WHITE)
            d.ellipse((108, y + 12, 162, y + 66), fill=(46, 160, 90))
            d.line([(122, y + 40), (133, y + 52), (150, y + 26)], fill=WHITE, width=7)
            d.text((180, y + 16), lab, font=F(BLACK, 40), fill=TEAL_XDK)
    return im


def overlay_box(lines, sub=None, color=GOLD):
    """bandeau texte semi-transparent en haut (pour poser sur un plan IA)"""
    def f(frame, t, dur):
        im = frame.convert('RGBA')
        k = ease(t / 0.45)
        ov = Image.new('RGBA', im.size, (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
        y0 = 150 - int((1 - k) * 60)
        h = 110 + 95 * (len(lines) - 1) + (60 if sub else 0)
        rrect(d, (40, y0, 680, y0 + h), 30, (7, 46, 45, int(225 * k)))
        for i, (txt, size, col) in enumerate(lines):
            w = d.textlength(txt, font=F(BLACK, size))
            d.text(((W - w) / 2, y0 + 22 + i * 95), txt, font=F(BLACK, size), fill=col + (int(255 * k),))
        if sub:
            w = d.textlength(sub, font=F(BOLD, 32))
            d.text(((W - w) / 2, y0 + h - 62), sub, font=F(BOLD, 32), fill=(220, 235, 233, int(255 * k)))
        return Image.alpha_composite(im, ov)
    return f


def render_over(name, src, start, dur, fn):
    """applique fn sur les images d'un plan vidéo"""
    out = D + f'M_{name}.mp4'
    dec = subprocess.Popen(['ffmpeg', '-v', 'error', '-ss', str(start), '-t', str(dur), '-i', D + src, '-vf',
                            f'scale={W}:{int(W*1280/704)//2*2},crop={W}:{H},fps={FPS}', '-f', 'rawvideo',
                            '-pix_fmt', 'rgb24', '-'], stdout=subprocess.PIPE)
    enc = subprocess.Popen(['ffmpeg', '-v', 'error', '-y', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
                            '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-crf', '18', '-pix_fmt', 'yuv420p', out],
                           stdin=subprocess.PIPE)
    n = 0; last = None
    while True:
        b = dec.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        last = Image.frombytes('RGB', (W, H), b)
        enc.stdin.write(fn(last, n / FPS, dur).convert('RGB').tobytes()); n += 1
    while n < int(round(dur * FPS)) and last is not None:  # tenir la dernière image si le plan est trop court
        enc.stdin.write(fn(last, n / FPS, dur).convert('RGB').tobytes()); n += 1
    enc.stdin.close(); enc.wait(); print('ok', out, n / FPS)


def compare(t, dur):  # brouette vs maison
    im = base(); d = ImageDraw.Draw(im)
    br = cover(D + 'brouette.jpg', 320, 420)
    ma = cover(A + 'd5012_r0.webp', 320, 420)
    k1 = ease(t / 0.4); k2 = ease((t - 0.8) / 0.4)
    for img, x, k, top, bot, col in [(br, 30, k1, '39 000 FCFA', '1 brouette', GOLD), (ma, 370, k2, 'DES MILLIONS', 'votre maison', ORANGE)]:
        if k <= 0:
            continue
        m = Image.new('L', img.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 319, 419), 26, fill=255)
        y = 300 + int((1 - k) * 80)
        im.paste(img, (x, y), m)
        w = d.textlength(top, font=F(BLACK, 44)); d.text((x + 160 - w / 2, y - 70), top, font=F(BLACK, 44), fill=col)
        w = d.textlength(bot, font=F(BOLD, 34)); d.text((x + 160 - w / 2, y + 440), bot, font=F(BOLD, 34), fill=WHITE)
    k3 = ease((t - 1.8) / 0.5)
    if k3 > 0:
        ctext(d, 170, 'LA MEILLEURE DÉPENSE', F(BLACK, 50), WHITE)
        ctext(d, 930, 'de tout votre chantier', F(BLACK, 50), GOLD)
    return im


def deux_bonus(t, dur):
    im = base(); d = ImageDraw.Draw(im)
    s = pop(t / 0.6)
    gift = Image.new('RGBA', (300, 300), (0, 0, 0, 0)); g = ImageDraw.Draw(gift)
    g.rounded_rectangle((30, 110, 270, 290), 20, fill=ORANGE); g.rectangle((20, 80, 280, 140), fill=(212, 115, 26))
    g.rectangle((135, 80, 165, 290), fill=GOLD); g.ellipse((80, 20, 150, 90), outline=GOLD, width=16); g.ellipse((150, 20, 220, 90), outline=GOLD, width=16)
    paste_scaled(im, gift, W / 2, 470, s)
    ctext(d, 700, '+ 2 BONUS', F(BLACK, 110), GOLD)
    ctext(d, 840, 'OFFERTS', F(BLACK, 90), WHITE)
    return im


def bonus1(t, dur):
    im = base(); d = ImageDraw.Draw(im)
    k = ease(t / 0.4)
    rrect(d, (40, 120, 680, 340), 30, ORANGE)
    ctext(d, 145, 'BONUS 1', F(BLACK, 46), WHITE)
    ctext(d, 205, 'Les nouveaux plans', F(BLACK, 52), WHITE)
    ctext(d, 268, 'gratuits à vie', F(BLACK, 52), TEAL_XDK)
    R = renders_list()
    for j in range(3):
        kk = ease((t - 1.0 - j * 0.9) / 0.45)
        if kk <= 0:
            continue
        r = R[(j * 4 + 2) % len(R)].resize((300, 188))
        x = 50 + (j % 2) * 320; y = 400 + (j // 2) * 230
        if j == 2:
            x = 210
        m = Image.new('L', r.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, 299, 187), 20, fill=255)
        im.paste(r, (x, y + int((1 - kk) * 60)), m)
        rrect(d, (x + 200, y + 10, x + 290, y + 52), 12, (46, 160, 90))
        d.text((x + 214, y + 14), 'NEW', font=F(BLACK, 28), fill=WHITE)
    return im


def whatsapp(t, dur):
    im = Image.new('RGB', (W, H), (236, 229, 221)); d = ImageDraw.Draw(im)
    d.rectangle((0, 0, W, 150), fill=(7, 94, 84))
    d.ellipse((30, 45, 100, 115), fill=GOLD)
    d.text((48, 58), 'A', font=F(BLACK, 40), fill=TEAL_XDK)
    d.text((120, 50), 'Architecte WooPlans', font=F(XB, 34), fill=WHITE)
    d.text((120, 95), 'en ligne', font=F(MED, 26), fill=(200, 230, 220))
    msgs = [(False, 'Mon terrain fait 15 m sur 25 m.\nLe duplex va passer ?'),
            (True, 'Oui ! On peut l\'adapter à votre\nterrain. Vous voulez combien\nde chambres ?'),
            (False, '4 chambres et un garage.'),
            (True, 'Parfait, je vous montre les\nmodèles qui conviennent 👌')]
    y = 190
    for i, (me, txt) in enumerate(msgs):
        k = ease((t - 0.2 - i * 0.75) / 0.25)
        if k <= 0:
            break
        lines = txt.split('\n'); h = 30 + 44 * len(lines)
        wmax = max(d.textlength(l, font=F(MED, 32)) for l in lines) + 44
        x = W - 30 - wmax if me else 30
        rrect(d, (x, y, x + wmax, y + h), 22, (220, 248, 198) if me else WHITE)
        for j, l in enumerate(lines):
            d.text((x + 22, y + 14 + j * 44), l.replace('👌', ''), font=F(MED, 32), fill=(30, 30, 30))
        y += h + 24
    return im


def garantie(t, dur):
    im = base(); d = ImageDraw.Draw(im)
    s = pop(t / 0.6)
    badge = Image.new('RGBA', (460, 460), (0, 0, 0, 0)); b = ImageDraw.Draw(badge)
    for i in range(24):
        a = i * math.pi / 12
        b.polygon([(230 + 225 * math.cos(a), 230 + 225 * math.sin(a)), (230 + 190 * math.cos(a + 0.13), 230 + 190 * math.sin(a + 0.13)),
                   (230 + 190 * math.cos(a - 0.13), 230 + 190 * math.sin(a - 0.13))], fill=GOLD)
    b.ellipse((40, 40, 420, 420), fill=GOLD); b.ellipse((65, 65, 395, 395), outline=TEAL_XDK, width=6)
    for txt, y, sz in [('7', 105, 150), ('JOURS', 270, 50)]:
        w = b.textlength(txt, font=F(BLACK, sz)); b.text((230 - w / 2, y), txt, font=F(BLACK, sz), fill=TEAL_XDK)
    paste_scaled(im, badge, W / 2, 470, s * (1 + 0.02 * math.sin(t * 3)))
    ctext(d, 760, 'SATISFAIT', F(BLACK, 80), WHITE)
    ctext(d, 850, 'OU REMBOURSÉ', F(BLACK, 80), GOLD)
    return im


def prix(t, dur):
    im = base(); d = ImageDraw.Draw(im)
    ctext(d, 170, 'PRIX ACTUEL', F(BLACK, 64), WHITE)
    s = pop(t / 0.6)
    p = Image.new('RGBA', (640, 200), (0, 0, 0, 0)); pd = ImageDraw.Draw(p)
    pd.rounded_rectangle((0, 0, 639, 199), 40, fill=ORANGE)
    w = pd.textlength('39 000 FCFA', font=F(BLACK, 104)); pd.text((320 - w / 2, 36), '39 000 FCFA', font=F(BLACK, 104), fill=WHITE)
    paste_scaled(im, p, W / 2, 380, s)
    items = ['Un seul paiement', 'Accès immédiat et à vie', 'Mobile Money ou carte']
    for i, txt in enumerate(items):
        k = ease((t - 1.2 - i * 1.3) / 0.4)
        if k <= 0:
            continue
        y = 560 + i * 110
        d.ellipse((90, y + 6, 150, y + 66), fill=(46, 160, 90))
        d.line([(106, y + 36), (118, y + 49), (136, y + 22)], fill=WHITE, width=7)
        d.text((175 + (1 - k) * 60, y + 8), txt, font=F(BLACK, 46), fill=WHITE)
    return im


def final(t, dur):
    global COVER
    catalogue(0, 1)
    im = base(); d = ImageDraw.Draw(im)
    paste_scaled(im, COVER, W / 2, 470, 0.78)
    rrect(d, (90, 870, 630, 980), 30, ORANGE)
    ctext(d, 890, '39 000 FCFA', F(BLACK, 70), WHITE)
    ctext(d, 1020, '👇 Cliquez sous la vidéo'.replace('👇 ', ''), F(BLACK, 46), GOLD)
    ctext(d, 1090, 'wooplans.com', F(BOLD, 38), WHITE)
    return im


CLIPS = {
    'budget': (1.8, budget), 'propositions': (3.9, propositions), 'catalogue': (3.2, catalogue), 'cent': (3.2, cent),
    'plan': (4.1, plan), 'devis': (6.5, devis), 'terrain': (7.3, terrain), 'compare': (4.3, compare),
    'deux_bonus': (3.7, deux_bonus), 'bonus1': (9.1, bonus1), 'whatsapp': (3.0, whatsapp), 'garantie': (8.1, garantie),
    'prix': (8.2, prix), 'final': (2.6, final),
}

if __name__ == '__main__':
    for n in sys.argv[1:]:
        if n == 'ov_chantier':
            render_over(n, 'B_chantier.mp4', 0, 5.6, overlay_box([('12 ANS DE MÉTIER', 54, GOLD), ('250+ CHANTIERS', 54, WHITE)], 'suivis par nos équipes'))
        elif n == 'ov_brouette':
            render_over(n, 'B_brouette.mp4', 0, 4.9, overlay_box([('39 000 FCFA', 70, GOLD), ('≈ 1 brouette', 56, WHITE)], '(une brouette ≈ 35 000 FCFA)'))
        else:
            dur, fn = CLIPS[n]; render(n, dur, fn)
