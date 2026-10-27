from common import *
from seq_intro import kb

SH = [  # t0, label, fichier, z0, z1, p0, p1, night
 (0.0, 'Façade principale', 'R0.png', 1.0, 1.10, (0.5, 0.55), (0.5, 0.5), 0),
 (7.1, 'Volume principal', 'R0.png', 1.5, 1.9, (0.28, 0.5), (0.30, 0.52), 0),
 (11.8, 'Garage deux voitures', 'R0.png', 1.5, 2.0, (0.74, 0.58), (0.76, 0.6), 0),
 (16.6, 'Pierre apparente', 'R0.png', 1.8, 2.4, (0.46, 0.45), (0.46, 0.40), 0),
 (22.5, 'Vue trois quarts', 'R4.png', 1.0, 1.2, (0.5, 0.5), (0.45, 0.5), 0),
 (28.5, 'Garage intégré', 'R2.png', 1.0, 1.25, (0.45, 0.55), (0.40, 0.55), 0),
 (31.0, 'Vue du ciel', 'R3.png', 1.0, 1.25, (0.5, 0.45), (0.5, 0.55), 0),
 (36.5, "Côté entrée", 'R1.png', 1.0, 1.25, (0.5, 0.5), (0.45, 0.55), 0),
 (41.0, 'Façade latérale', 'R5.png', 1.0, 1.3, (0.5, 0.5), (0.45, 0.5), 0),
 (47.9, 'Le soir tombe', 'R6.png', 1.0, 1.25, (0.5, 0.5), (0.4, 0.55), 0),
 (55.2, 'Lumière chaude', 'R6.png', 1.5, 2.0, (0.45, 0.45), (0.48, 0.5), 0),
 (56.4, 'Côté garage', 'R8.png', 1.0, 1.2, (0.5, 0.5), (0.55, 0.5), 0),
 (59.7, 'Vue arrière', 'R9.png', 1.0, 1.25, (0.5, 0.5), (0.5, 0.55), 0),
 (64.3, 'Vue du soir', 'R7.png', 1.0, 1.15, (0.5, 0.5), (0.5, 0.52), 0),
]
words = words_of('rendus')
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
    na = clamp((t - 67.6) / 0.4) * clamp((DUR - 0.4 - t) / 0.4)
    if na > 0.02:
        msg = 'Dalles, plantes, voitures, personnages : décor, hors devis'
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
