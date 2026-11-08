from common import *
from seq_intro import kb

words = words_of('rendus')
_f = lambda p, n=0: find(words, p, n)
SH = [  # t0, label, fichier, z0, z1, p0, p1, night
 (0.0, 'Vue de face', 'R0.png', 1.0, 1.10, (0.5, 0.55), (0.5, 0.5), 0),
 (_f('toiture') - 0.2, 'Toiture à plusieurs pentes', 'R0.png', 1.6, 1.6, (0.28, 0.25), (0.72, 0.25), 0),
 (_f('arcades') - 0.2, 'Deux arcades', 'R0.png', 1.9, 2.2, (0.5, 0.42), (0.5, 0.42), 0),
 (_f('colonnes') - 0.2, 'Colonnes blanches', 'R0.png', 2.4, 2.4, (0.29, 0.5), (0.72, 0.5), 0),
 (_f('bandes') - 0.2, 'Bandes de bois', 'R0.png', 2.0, 2.0, (0.12, 0.45), (0.88, 0.45), 0),
 (_f('changeons') - 0.1, 'Vue trois quarts', 'R1.png', 1.0, 1.2, (0.5, 0.5), (0.45, 0.5), 0),
 (_f('terrasse') - 0.2, 'Terrasse couverte', 'R1.png', 1.7, 2.1, (0.58, 0.58), (0.64, 0.6), 0),
 (_f('passons') - 0.1, 'Façade latérale', 'R3.png', 1.0, 1.2, (0.5, 0.5), (0.45, 0.55), 0),
 (_f('base') - 0.3, 'Base en pierre', 'R3.png', 2.0, 2.0, (0.28, 0.64), (0.58, 0.66), 0),
 (_f('regardons') - 0.1, "L'autre côté", 'R2.png', 1.0, 1.2, (0.5, 0.5), (0.55, 0.45), 0),
 (_f('toiture', 1) - 0.2, 'La toiture se déploie', 'R2.png', 1.5, 1.5, (0.75, 0.2), (0.45, 0.2), 0),
 (_f('terrasse', 1) - 0.2, 'Terrasse au bout', 'R2.png', 1.8, 2.1, (0.3, 0.45), (0.26, 0.5), 0),
 (_f('soir') - 0.4, 'Le soir tombe', 'R4.png', 1.0, 1.2, (0.5, 0.5), (0.45, 0.5), 0),
 (_f('lumières') - 0.2, 'Lumière chaude', 'R4.png', 1.7, 2.0, (0.5, 0.45), (0.55, 0.5), 0),
 (_f('même') - 0.2, 'Côté latéral, la nuit', 'R5.png', 1.0, 1.3, (0.5, 0.5), (0.45, 0.5), 0),
 (_f('spots') - 0.2, 'Spots dans les avant-toits', 'R5.png', 1.6, 1.9, (0.4, 0.3), (0.55, 0.3), 0),
 (_f('finir') - 0.3, 'Vue du soir', 'R6.png', 1.0, 1.2, (0.5, 0.5), (0.4, 0.55), 0),
]
DUR = D['rendus']
NS = len(SH)
BOUNDS = [s[0] for s in SH] + [DUR]
SRCS = [Image.open(A + s[2]).convert('RGB') for s in SH]
FADE = 0.55


def night(im, k):
    # passage de l'heure dorée à l'heure bleue
    import numpy as np
    a = np.asarray(im).astype('float32') / 255.0
    tint = np.array([0.50, 0.62, 0.98], dtype='float32')
    dark = 0.55
    g = a * tint * dark
    # conserver les lumières chaudes (fenêtres) : zones lumineuses et chaudes
    lum = a.mean(axis=2, keepdims=True)
    warm = np.clip((a[..., 0:1] - a[..., 2:3]) * 2.2, 0, 1) * np.clip((lum - 0.55) * 3, 0, 1)
    g = g * (1 - warm) + a * warm * 1.05
    out = a * (1 - k) + g * k
    return Image.fromarray((np.clip(out, 0, 1) * 255).astype('uint8'))


def shot(i, t):
    t0 = BOUNDS[i]; t1 = BOUNDS[i + 1] + (FADE if i < NS - 1 else 0)
    _, _, _, z0, z1, p0, p1, nt = SH[i]
    im = kb(SRCS[i], t - t0, t1 - t0, z0, z1, p0, p1)
    if nt:
        im = night(im, clamp((t - t0) / 3.5))
    return im


def frame(t):
    i = 0
    for k in range(NS):
        if t >= BOUNDS[k]:
            i = k
    im = shot(i, t)
    if i > 0 and t < BOUNDS[i] + FADE:
        prev = shot(i - 1, t)
        im = Image.blend(prev, im, e_io((t - BOUNDS[i]) / FADE))
    base = im.convert('RGBA')
    g = Image.new('RGBA', (W, 330), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for y in range(330):
        gd.line((0, y, W, y), fill=(8, 28, 30, int(150 * (y / 330) ** 1.5)))
    base.alpha_composite(g, (0, H - 330))
    d = ImageDraw.Draw(base)
    rrect(d, (56, 44, 56 + 420, 44 + 84), 42, fill=ORANGE + (255,))
    d.text((56 + 210, 86), 'RENDUS 3D', font=font(40), fill=WHITE, anchor='mm')
    ts = BOUNDS[i]
    p = e_back((t - ts - 0.1) / 0.35)
    lab = SH[i][1]
    wch = int(tw(lab, 46) + 70)
    if p > 0.02:
        yy = 150 - int((1 - clamp(p, 0, 1)) * 30)
        ov = Image.new('RGBA', (wch, 84), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle((0, 0, wch - 1, 83), 42, fill=GREEN + (int(240 * clamp(p)),))
        od.text((wch // 2, 42), lab, font=font(46), fill=WHITE + (int(255 * clamp(p)),), anchor='mm')
        base.alpha_composite(ov, (56, yy))
    lg = img('logo_white.png').copy(); lg.thumbnail((230, 130)); base.alpha_composite(lg, (W - 56 - lg.width, 36))
    for k in range(NS):
        x = W - 70 - (NS - 1 - k) * 40
        d.ellipse((x - 11, 1000 - 11, x + 11, 1000 + 11), fill=WHITE + (255,) if k <= i else (255, 255, 255, 90))
    # note « hors devis »
    na = clamp((t - (_f('précision') - 0.1)) / 0.4) * clamp((DUR - 0.4 - t) / 0.4)
    if na > 0.02:
        msg = 'Dalles, plantes, décor : pour l\'ambiance, hors devis'
        wn = int(tw(msg, 40) + 80)
        ov = Image.new('RGBA', (wn, 90), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rounded_rectangle((0, 0, wn - 1, 89), 45, fill=WHITE + (int(240 * na),))
        od.text((wn // 2, 45), msg, font=font(40), fill=DARK + (int(255 * na),), anchor='mm')
        base.alpha_composite(ov, ((W - wn) // 2 - 40, 860))
    return base.convert('RGB')


if __name__ == '__main__':
    import sys
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_rendus_{tt:05.1f}.png')
