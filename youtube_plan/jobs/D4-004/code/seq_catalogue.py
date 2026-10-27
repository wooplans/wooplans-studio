from common import *
from widgets import *
DUR = D['catalogue']
NF = 919
_cache = {}

def capf(c):
    """image du téléphone au temps de capture c (secondes depuis 4.0 s), interpolée"""
    x = clamp((c - 4.0) * 30, 0, NF - 1.001)
    i = int(x); fr = x - i
    def get(k):
        if k not in _cache:
            _cache[k] = Image.open(A + f'cap/f_{k + 1:05d}.jpg').convert('RGB')
        return _cache[k]
    a = get(i)
    return a if fr < 0.05 else Image.blend(a, get(i + 1), fr)

# segments : (v0, v1, c0, c1)
SEG = [(5.8, 14.3, 4.0, 9.1), (14.3, 20.3, 9.3, 9.9), (20.3, 23.6, 15.4, 20.6), (23.6, 29.2, 26.6, 32.4), (29.2, 36.0, 33.0, 34.2)]

def phone_img(t):
    for k, (v0, v1, c0, c1) in enumerate(SEG):
        if v0 <= t < v1 or k == len(SEG) - 1:
            u = clamp((t - v0) / (v1 - v0)); im = capf(lerp(c0, c1, u))
            if k > 0 and t - v0 < 0.3 and abs(SEG[k - 1][3] - c0) > 0.5:
                pv = capf(SEG[k - 1][3]); im = Image.blend(pv, im, e_io((t - v0) / 0.3))
            return im
    return capf(4.0)

STEPS = [  # t0, t1, icône, ligne1, ligne2
 (6.0, 9.3, '', 'Nos meilleurs plans', 'de villas et de duplex'),
 (9.3, 12.3, '', 'Réunis dans un', 'seul catalogue'),
 (12.3, 14.4, '', 'Lien dans', 'la description'),
 (14.5, 17.6, '', '1. Vous choisissez', 'votre future maison'),
 (17.6, 20.4, '', '2. Vous ouvrez', 'sa fiche'),
 (20.4, 23.5, '', 'Distributions cotées', 'avec toutes les dimensions'),
 (23.5, 29.2, '', 'Devis estimatif', 'poste par poste, selon votre pays'),
 (29.2, 32.3, '', 'Catalogue Premium', 'WooPlans'),
]
PH_X, PH_Y = 480, 150     # coin haut-gauche de l'écran du téléphone
_bg = None

def bg():
    global _bg
    if _bg is None:
        b = Image.new('RGBA', (W, H), GREEN + (255,))
        gd = ImageDraw.Draw(b)
        for y in range(H): gd.line((0, y, W, y), fill=(int(lerp(15, 8, y / H)), int(lerp(91, 60, y / H)), int(lerp(89, 58, y / H)), 255))
        lg = img('logo_white.png').copy(); lg.thumbnail((700, 460)); paste_alpha(b, lg, (W // 2 - 350 + 250, H // 2 - 200), 0.05)
        _bg = b
    return _bg

def frame(t):
    base = bg().copy(); d = ImageDraw.Draw(base)
    lg = img('logo_white.png').copy(); lg.thumbnail((230, 130)); base.alpha_composite(lg, (56, 36))
    # --- titre pause (0 -> 6)
    ta = e_out((t - 3.7) / 0.5) * (1 - e_io((t - 5.7) / 0.5))
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    k0 = e_out(t / 0.5) * (1 - e_io((t - 3.5) / 0.4))
    text(od, (960, 470), 'Le budget, dans un instant…', 72, WHITE, 'mm')
    base.alpha_composite(fade_(ov, k0))
    if ta > 0.01:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.ellipse((960 - 130, 330 - 130 + 60, 960 + 130, 330 + 130 + 60), fill=ORANGE + (255,))
        od.rectangle((960 - 52, 330 - 62 + 60, 960 - 18, 330 + 62 + 60), fill=WHITE); od.rectangle((960 + 18, 330 - 62 + 60, 960 + 52, 330 + 62 + 60), fill=WHITE)
        text(od, (960, 640), 'UNE PETITE PAUSE', 76, WHITE, 'mm')
        base.alpha_composite(fade_(ov, ta))
    # --- téléphone
    pk = e_out((t - 5.6) / 0.7) * (1 - e_io((t - 32.0) / 0.6))
    if pk > 0.01:
        ph = Image.new('RGBA', (398 + 44, 800 + 44), (0, 0, 0, 0)); pd = ImageDraw.Draw(ph)
        pd.rounded_rectangle((0, 0, 441, 843), 58, fill=(18, 24, 30, 255), outline=(70, 80, 90, 255), width=3)
        sc = phone_img(t)
        m = Image.new('L', sc.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, sc.width - 1, sc.height - 1), 40, fill=255)
        ph.paste(sc, (22, 22), m)
        pd.rounded_rectangle((441 // 2 - 46, 10, 441 // 2 + 46, 20), 6, fill=(40, 48, 56, 255))
        sl = (1 - pk) * 160
        shadow = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        base2 = base
        px, py = PH_X - 22, int(PH_Y - 22 + sl + (60 * e_io((t - 32.0) / 0.6)))
        if pk < 1: ph.putalpha(ph.getchannel('A').point(lambda v: int(v * pk)))
        base.alpha_composite(ph, (px, py))
    # --- étapes à droite
    for (t0, t1, ch, l1, l2) in STEPS:
        a = e_back((t - t0) / 0.4) * (1 - e_io((t - (t1 - 0.25)) / 0.3)) if t1 < 32.3 else e_back((t - t0) / 0.4) * (1 - e_io((t - 32.0) / 0.5))
        if t < t0 or a <= 0.02: continue
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        x0, y0, x1, y1 = 1050, 380, 1840, 640
        shadow_card(ov, (x0, y0, x1, y1), r=36); od = ImageDraw.Draw(ov)
        od.ellipse((x0 + 36, y0 + 60, x0 + 176, y0 + 200), fill=ORANGE + (255,))
        icon(od, (x0 + 106, y0 + 130), ch, 62, WHITE)
        od.text((x0 + 210, y0 + 100), l1, font=font(46), fill=DARK, anchor='lm')
        od.text((x0 + 210, y0 + 165), l2, font=font(30 if len(l2) > 24 else 40), fill=GREEN, anchor='lm')
        s = clamp(a, 0, 1.06)
        ov = ov.crop((x0 - 60, y0 - 60, x1 + 60, y1 + 60))
        ov = ov.resize((int(ov.width * s), int(ov.height * s)), Image.LANCZOS)
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * clamp(a))))
        base.alpha_composite(ov, (cx - ov.width // 2, cy - ov.height // 2))
    # --- fin : On reprend !
    ra = e_back((t - 32.3) / 0.45)
    if ra > 0.02:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        s = int(150 * clamp(ra, 0, 1.08))
        text(od, (960, 520), 'On reprend !', max(10, s), WHITE, 'mm', stroke=0)
        od.polygon([(960 - 40, 700), (960 - 40, 780), (960 + 40, 740)], fill=ORANGE + (255,))
        base.alpha_composite(fade_(ov, clamp(ra)))
    return base.convert('RGB')

def fade_(ov, a):
    if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * clamp(a))))
    return ov

if __name__ == '__main__':
    import sys
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_cat_{tt:05.1f}.png')
