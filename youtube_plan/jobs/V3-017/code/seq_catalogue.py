from common import *
from widgets import *
DUR = D['catalogue']
SW, SH_ = 398, 800
LGREEN = (15, 91, 89)
_c = {}
def _img(path, w=None):
    if path not in _c:
        im = Image.open(path).convert('RGB')
        _c[path] = im
    im = _c[path]
    if w: im = im.resize((w, int(im.height * w / im.width)), Image.LANCZOS)
    return im
OTHER = A.replace('V3-017', 'D4-040')

def _top(d, im):
    d.rectangle((0, 0, SW, 78), fill=WHITE)
    lg = img('logo_green.png').copy(); lg.thumbnail((120, 44)); im.paste(lg, (16, 18), lg if lg.mode == 'RGBA' else None)
    d.rounded_rectangle((SW - 120, 26, SW - 16, 52), 13, fill=ORANGE); d.text((SW - 68, 39), 'PREMIUM', font=font(13), fill=WHITE, anchor='mm')
    d.line((0, 78, SW, 78), fill=(226, 232, 236), width=2)

def _card(im, y, src, name, meta, tag=None):
    d = ImageDraw.Draw(im)
    d.rounded_rectangle((16, y, SW - 16, y + 330), 22, fill=WHITE, outline=(226, 232, 236), width=2)
    ph = _img(src, SW - 56); ph = ph.crop((0, max(0, (ph.height - 210) // 2), ph.width, max(0, (ph.height - 210) // 2) + 210))
    m = Image.new('L', ph.size, 0); ImageDraw.Draw(m).rounded_rectangle((0, 0, ph.width - 1, ph.height - 1), 14, fill=255)
    im.paste(ph, (28, y + 12), m)
    if tag:
        d.rounded_rectangle((40, y + 24, 118, y + 50), 13, fill=ORANGE); d.text((79, y + 37), tag, font=font(14), fill=WHITE, anchor='mm')
    d.text((32, y + 252), name, font=font(24), fill=DARK, anchor='lm')
    d.text((32, y + 290), meta, font=font(16), fill=GREY, anchor='lm')

def scr_list(u):
    im = Image.new('RGB', (SW, SH_), (243, 245, 247)); d = ImageDraw.Draw(im)
    off = int(u * 180)
    _card(im, 100 - off, A + 'R1.png', 'Villa V3-017', '3 chambres · 120 m² · plain-pied', 'Nouveau')
    _card(im, 450 - off, OTHER + 'R1.png', 'Duplex D4-040', '4 chambres · 155 m² · R+1')
    d.rectangle((0, 0, SW, 78), fill=WHITE); _top(d, im)
    return im

def scr_fiche(u):
    im = Image.new('RGB', (SW, SH_), WHITE); d = ImageDraw.Draw(im)
    ph = _img(A + 'R1.png', SW).crop((0, 0, SW, 250)); im.paste(ph, (0, 78))
    for k in range(5):
        t_ = _img(A + f'R{k}.png', 66).crop((0, 0, 66, 44)); im.paste(t_, (14 + k * 76, 340))
        if k == 0: d.rectangle((14, 340, 80, 384), outline=ORANGE, width=3)
    d.text((18, 420), 'VILLA · RÉF. V3-017', font=font(14), fill=GREY, anchor='lm')
    d.text((18, 456), 'Villa V3-017', font=font(30), fill=DARK, anchor='lm')
    for k, lab in enumerate(('3 chambres', '120 m²', '1 niveau')):
        w = int(tw(lab, 18) + 30); x = 18 + sum(int(tw(l, 18) + 42) for l in ('3 chambres', '120 m²', '1 niveau')[:k])
        d.rounded_rectangle((x, 492, x + w, 530), 19, fill=(235, 244, 243)); d.text((x + w / 2, 511), lab, font=font(18), fill=LGREEN, anchor='mm')
    d.rounded_rectangle((18, 560, 190, 604), 22, outline=(200, 208, 214), width=2); d.text((104, 582), 'Ajouter aux favoris', font=font(14), fill=DARK, anchor='mm')
    d.rounded_rectangle((204, 560, 300, 604), 22, outline=(200, 208, 214), width=2); d.text((252, 582), 'Comparer', font=font(14), fill=DARK, anchor='mm')
    d.rounded_rectangle((18, 626, 380, 690), 18, fill=LGREEN); d.text((199, 658), 'Fiche PDF · plans · devis', font=font(20), fill=WHITE, anchor='mm')
    _top(d, im)
    return im

def scr_plan(u):
    im = Image.new('RGB', (SW, SH_), WHITE); d = ImageDraw.Draw(im)
    d.text((18, 120), 'Distributions', font=font(26), fill=DARK, anchor='lm')
    pl = _img(A + 'rdc3d.png', SW - 36); y = 170 - int(u * 40)
    d.rounded_rectangle((12, y - 8, SW - 12, y + pl.height + 8), 16, outline=(226, 232, 236), width=2)
    im.paste(pl, (18, y)); d.text((SW // 2, y + pl.height + 34), 'PLAN DU REZ-DE-CHAUSSÉE', font=font(14), fill=GREY, anchor='mm')
    _top(d, im)
    return im

LOTS = [('Fondation', '2 419 200'), ('Élévations', '3 542 400'), ('Charpente et toiture', '2 678 400'), ('Crépissage et antivols', '2 534 400'),
        ('Portes et fenêtres', '1 900 800'), ('Plomberie et électricité', '1 584 000'), ('Plafond et peinture', '2 217 600'), ('Carrelage', '2 323 200')]
def scr_devis(u):
    im = Image.new('RGB', (SW, SH_), WHITE); d = ImageDraw.Draw(im)
    d.text((18, 122), 'Devis estimatif détaillé', font=font(24), fill=DARK, anchor='lm')
    d.text((18, 152), 'Montants indicatifs, selon le pays', font=font(14), fill=GREY, anchor='lm')
    off = int(u * 130)
    for i, (lab, amt) in enumerate(LOTS):
        y = 190 + i * 54 - off
        if y < 168: continue
        d.line((18, y + 46, SW - 18, y + 46), fill=(232, 236, 240), width=2)
        d.text((18, y + 22), lab, font=font(17), fill=DARK, anchor='lm'); d.text((SW - 18, y + 22), amt + ' FCFA', font=font(15), fill=GREY, anchor='rm')
    _top(d, im)
    return im

def scr_brand(u):
    im = Image.new('RGB', (SW, SH_), LGREEN); d = ImageDraw.Draw(im)
    lg = img('logo_white.png').copy(); lg.thumbnail((260, 200)); im.paste(lg, ((SW - lg.width) // 2, 250), lg if lg.mode == 'RGBA' else None)
    d.text((SW // 2, 480), 'Catalogue Premium', font=font(30), fill=WHITE, anchor='mm'); d.text((SW // 2, 525), 'WooPlans', font=font(30), fill=GOLD, anchor='mm')
    return im

SEG = [(5.8, 14.3, scr_list), (14.3, 20.3, scr_fiche), (20.3, 23.6, scr_plan), (23.6, 29.2, scr_devis), (29.2, 36.0, scr_brand)]

def phone_img(t):
    for k, (v0, v1, fn) in enumerate(SEG):
        if v0 <= t < v1 or k == len(SEG) - 1:
            u = clamp((t - v0) / (v1 - v0)); im = fn(e_io(u))
            if k > 0 and t - v0 < 0.3:
                pv = SEG[k - 1][2](1.0); im = Image.blend(pv, im, e_io((t - v0) / 0.3))
            return im
    return SEG[0][2](0)

STEPS = [  # t0, t1, icône, ligne1, ligne2
 (6.0, 9.3, '', 'Nos meilleurs plans', 'de villas et de duplex'),
 (9.3, 12.3, '', 'Réunis dans un', 'seul catalogue'),
 (12.3, 14.4, '', 'Lien dans', 'la description'),
 (14.5, 17.6, '', '1. Vous choisissez', 'votre future maison'),
 (17.6, 20.4, '', '2. Vous ouvrez', 'sa fiche'),
 (20.4, 23.5, '\uf0e8', 'Les plans', 'avec les surfaces des pièces'),
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
