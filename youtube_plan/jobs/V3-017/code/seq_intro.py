from common import *
from widgets import fa, icon

def L(n): return Image.open(A + n).convert('RGB')
R = [L(f'R{i}.png') for i in range(7)]
TH = Image.open(A + 'thumb_1920.png').convert('RGB')
PL1 = Image.open(A + 'rdc3d.png').convert('RGB')
DUR = D['intro']
words = words_of('intro')
f = lambda p, n=0: find(words, p, n)

def kb(src, t, dur, z0=1.0, z1=1.12, p0=(0.5, 0.5), p1=(0.5, 0.5)):
    k = e_io(clamp(t / dur))
    z = lerp(z0, z1, k); px = lerp(p0[0], p1[0], k); py = lerp(p0[1], p1[1], k)
    sw, sh = src.size
    cw, ch = sw / z, sh / z
    x0 = clamp(px * sw - cw / 2, 0, sw - cw); y0 = clamp(py * sh - ch / 2, 0, sh - ch)
    return src.resize((W, H), Image.LANCZOS, box=(x0, y0, x0 + cw, y0 + ch))

def mk_plan(PL):
    def plan_shot(t, dur):
        bg = kb(R[0], t, dur, 1.3, 1.4).filter(ImageFilter.GaussianBlur(26)).convert('RGBA')
        bg.alpha_composite(Image.new('RGBA', (W, H), (15, 91, 89, 150)))
        s = lerp(0.92, 1.0, e_out(t / 0.6)) * lerp(1.0, 1.06, t / dur)
        pw = int(1120 * s); ph = int(pw * PL.height / PL.width)
        im = PL.resize((pw, ph), Image.LANCZOS).convert('RGBA')
        shadow_card(bg, ((W - pw) // 2 - 14, (H - ph) // 2 - 44, (W + pw) // 2 + 14, (H + ph) // 2 - 16), r=30)
        bg.alpha_composite(im, ((W - pw) // 2, (H - ph) // 2 - 30))
        return bg.convert('RGB')
    return plan_shot

def K(i, z0, z1, p0, p1):
    return lambda t, d: kb(R[i], t, d, z0, z1, p0, p1)

T = dict(
    tro=f('trois', 0), suite=f('suite'), arc=f('arcades'), decouv=f('découvrir'), mais=f('mais'), regardez=f('regardez-la'),
    toit=f('toiture'), arches=f('arches'), colonnes=f('colonnes'), bandes=f('bandes'), seul=f('seul'), salon=f('salon'), manger=f('manger'),
    cuisine=f('cuisine'), magasin=f('magasin'), dressing=f('dressing'), dans=f('dans'), plan=f('plan'), maison=f('maison'), angles=f('angles'),
    terrain=f('terrain'), budget=f('budget'), poste=f('poste'), alors=f('alors'), abo=f('abonnez-vous'), parti=f("c'est", 1))
T_SUB = T['abo'] - 0.4
T_END = DUR
SHOTS = [
    (0.0, T['tro'], lambda t, d: kb(TH, t, d, 1.0, 1.10, (0.5, 0.5), (0.5, 0.46))),
    (T['tro'], T['suite'], K(1, 1.0, 1.3, (0.5, 0.5), (0.45, 0.5))),
    (T['suite'], T['arc'], K(2, 1.0, 1.3, (0.5, 0.5), (0.3, 0.5))),
    (T['arc'], T['mais'], K(0, 1.5, 1.8, (0.45, 0.42), (0.5, 0.42))),
    (T['mais'], T['toit'], K(1, 1.0, 1.25, (0.5, 0.5), (0.5, 0.5))),
    (T['toit'], T['arches'] - 0.2, K(0, 1.6, 1.6, (0.28, 0.25), (0.72, 0.25))),
    (T['arches'] - 0.2, T['bandes'] - 0.2, K(1, 1.7, 2.0, (0.62, 0.45), (0.55, 0.45))),
    (T['bandes'] - 0.2, T['seul'], K(0, 2.0, 2.0, (0.15, 0.5), (0.85, 0.5))),
    (T['seul'], T['salon'], K(3, 1.0, 1.3, (0.5, 0.5), (0.45, 0.55))),
    (T['salon'], T['magasin'], K(5, 1.0, 1.3, (0.5, 0.5), (0.4, 0.55))),
    (T['magasin'], T['dans'], K(6, 1.0, 1.3, (0.5, 0.5), (0.4, 0.55))),
    (T['dans'], T['plan'], K(2, 1.0, 1.3, (0.5, 0.5), (0.55, 0.5))),
    (T['plan'], T['maison'], mk_plan(PL1)),
    (T['maison'], T['terrain'] - 0.1, K(3, 1.0, 1.3, (0.5, 0.5), (0.5, 0.58))),
    (T['terrain'] - 0.1, T['budget'] - 0.1, K(1, 1.0, 1.35, (0.5, 0.5), (0.5, 0.58))),
    (T['budget'] - 0.1, T['alors'], K(0, 1.5, 2.0, (0.72, 0.5), (0.74, 0.52))),
    (T['alors'], T_SUB + 2.0, K(2, 1.0, 1.25, (0.5, 0.5), (0.58, 0.5))),
    (T_SUB + 2.0, DUR, K(0, 1.2, 1.0, (0.6, 0.5), (0.5, 0.5))),
]
XF = 0.28

def base(t):
    i = max(j for j, s in enumerate(SHOTS) if s[0] <= t or j == 0)
    t0, t1, fn = SHOTS[i]
    cur = fn(t - t0, t1 - t0)
    if i > 0 and t - t0 < XF:
        p = e_io((t - t0) / XF)
        pt0, pt1, pfn = SHOTS[i - 1]
        prev = pfn(pt1 - pt0, pt1 - pt0)
        cur = Image.blend(prev, cur, p)
    return cur.convert('RGBA')

CH = [('Visite du plan', T['plan']), ('Les rendus', T['angles']), ('Le terrain', T['terrain']), ('Le budget', T['budget'])]
# puces animées : carte de présentation (début) + liste des espaces (milieu)
BUL = [('\uf236', '3 chambres', T['tro'], ORANGE), ('\uf015', 'Suite parentale', T['suite'] - 0.2, GREEN), ('\uf19c', 'Deux grandes arcades', T['arc'] - 0.6, ORANGE)]
CHIPS = [('\uf015', '1 seul niveau', T['seul']), ('\uf236', '3 chambres', f('chambres', 1)), ('\uf26c', '1 salon', T['salon']),
         ('\uf0f5', 'Salle à manger', T['manger']), ('\uf06d', 'Cuisine', T['cuisine']), ('\uf187', 'Magasin', T['magasin']), ('\uf290', 'Dressing', T['dressing'])]
SFX_TIMES = [T['tro'], T['suite'], T['arc'] - 0.6, T['plan'], T['angles'], T['terrain'], T['budget']] + [c[2] - 0.1 for c in CHIPS]
CHIP_END = T['dans'] - 0.2
SLIDE_OUT = T['mais'] + 0.3
POPS = [b[2] for b in BUL] + [c[2] - 0.1 for c in CHIPS]

def fade_(ov, a):
    if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * clamp(a))))
    return ov

def slide_card(im, t):
    p_in = e_out((t - 0.5) / 0.6); p_out = e_io((t - SLIDE_OUT) / 0.5)
    k = p_in * (1 - p_out)
    if k <= 0.01: return
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    nb = sum(1 for b in BUL if (t - b[2]) / 0.38 > 0.02)
    x0, y0, x1, y1 = 1400, 130, 1860, 130 + 125 + nb * 84 + (10 if nb else 0)
    off = int((1 - k) * 700)
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle((x0 + off, y0, x1 + off, y1), 26, fill=(10, 60, 58, 135))
    d.rounded_rectangle((x0 + off, y0, x0 + off + 18, y1), 9, fill=ORANGE)
    text(d, (x0 + 50 + off, y0 + 52), 'VILLA V3-017', 38, WHITE, 'lm')
    text(d, (x0 + 50 + off, y0 + 98), '1 niveau · 120 m²', 26, (225, 238, 235), 'lm')
    for i, (ch, lab, tt, col) in enumerate(BUL):
        p = e_back((t - tt) / 0.38)
        if p <= 0.02: continue
        yy = y0 + 160 + i * 84 + int((1 - clamp(p, 0, 1)) * 30)
        s = clamp(p, 0, 1.1)
        d.ellipse((x0 + 50 + off, yy - 28, x0 + 106 + off, yy + 28), fill=col)
        icon(d, (x0 + 78 + off, yy), ch, int(30 * s), WHITE)
        d.text((x0 + 124 + off, yy), lab, font=font(int(34 * (0.8 + 0.2 * s))), fill=WHITE, anchor='lm')
    im.alpha_composite(fade_(ov, 1))

def chips(im, t):
    if t < CHIPS[0][2] - 0.3 or t > CHIP_END + 0.5: return
    out = clamp((t - CHIP_END) / 0.4)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    for i, (ch, lab, tt) in enumerate(CHIPS):
        p = e_back((t - tt + 0.1) / 0.35)
        if p <= 0.02: continue
        wl = int(tw(lab, 34) + 112); y = 170 + i * 86
        off = int((1 - clamp(p, 0, 1)) * -120)
        d.rounded_rectangle((56 + off, y, 56 + wl + off, y + 74), 37, fill=(10, 60, 58, 150))
        d.ellipse((64 + off, y + 7, 131 + off, y + 67), fill=ORANGE if i % 2 == 0 else (30, 140, 135))
        icon(d, (98 + off, y + 37), ch, 30, WHITE)
        d.text((144 + off, y + 37), lab, font=font(34), fill=WHITE, anchor='lm')
    im.alpha_composite(fade_(ov, 1 - out))

def subscribe(im, t):
    t0 = T_SUB - 0.2
    p = e_back((t - t0) / 0.35)
    if p <= 0.02: return
    out = clamp((t - (T_SUB + 2.4)) / 0.3)
    if out >= 1: return
    clicked = t > t0 + 1.5
    w, h = 400, 96
    s = clamp(p, 0, 1.12) * (1 - 0.3 * out)
    ov = Image.new('RGBA', (w + 20, h + 20), (0, 0, 0, 0)); d = ImageDraw.Draw(ov)
    col = (60, 60, 60, 255) if clicked else (230, 30, 30, 255)
    d.rounded_rectangle((10, 10, w + 10, h + 10), 48, fill=col)
    d.text((10 + 235, 10 + h // 2), 'Abonné' if clicked else "S'abonner", font=font(38), fill=WHITE, anchor='mm')
    cx, cy = 10 + 58, 10 + h // 2
    d.ellipse((cx - 26, cy - 26, cx + 26, cy + 26), fill=WHITE)
    d.pieslice((cx - 13, cy - 17, cx + 13, cy + 9), 180, 360, fill=col[:3])
    d.polygon([(cx - 13, cy - 4), (cx + 13, cy - 4), (cx + 17, cy + 9), (cx - 17, cy + 9)], fill=col[:3])
    d.ellipse((cx - 4, cy + 10, cx + 4, cy + 18), fill=col[:3])
    ov = ov.resize((max(1, int(ov.width * s)), max(1, int(ov.height * s))), Image.LANCZOS)
    pos = (W - 80 - ov.width, 900 - ov.height // 2)
    im.alpha_composite(ov, pos)
    if t0 + 1.0 < t < t0 + 2.2:
        q = clamp((t - t0 - 1.0) / 0.5)
        cx2 = int(pos[0] + ov.width * 0.55 + (1 - e_out(q)) * 120); cy2 = int(pos[1] + ov.height * 0.6 + (1 - e_out(q)) * 90)
        d2 = ImageDraw.Draw(im)
        d2.polygon([(cx2, cy2), (cx2, cy2 + 46), (cx2 + 13, cy2 + 35), (cx2 + 30, cy2 + 35)], fill=WHITE, outline=DARK)

def frame(t):
    im = base(t)
    g = Image.new('RGBA', (W, 260), (0, 0, 0, 0)); gd = ImageDraw.Draw(g)
    for y in range(260): gd.line((0, y, W, y), fill=(8, 28, 30, int(120 * (y / 260) ** 1.6)))
    if t > 8.8: im.alpha_composite(g, (0, H - 260))
    la = clamp((t - 8.95) / 0.4)
    if la > 0:
        lg = img('logo_white.png').copy(); lg.thumbnail((230, 120))
        if la < 1: lg.putalpha(lg.getchannel('A').point(lambda v: int(v * la)))
        im.alpha_composite(lg, (56, 36))
    slide_card(im, t)
    chips(im, t)
    x = 470
    for lab, tt in CH:
        p = e_back((t - tt + 0.05) / 0.3)
        wch = int(tw(lab, 34) + 100)
        out = clamp((t - (T['alors'] - 0.2)) / 0.4)
        if p > 0.02 and out < 1:
            a = clamp(p) * (1 - out)
            yy = 930 - int((1 - clamp(p)) * 30)
            ov = Image.new('RGBA', (wch, 76), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
            od.rounded_rectangle((0, 0, wch - 1, 75), 38, fill=(10, 60, 58, int(170 * a)))
            od.ellipse((10, 10, 66, 66), fill=ORANGE + (int(255 * a),))
            od.text((38, 38), str([c[0] for c in CH].index(lab) + 1), font=font(32), fill=WHITE + (int(255 * a),), anchor='mm')
            od.text((82, 38), lab, font=font(34), fill=WHITE + (int(255 * a),), anchor='lm')
            im.alpha_composite(ov, (x, yy))
        x += wch + 22
    subscribe(im, t)
    fl = clamp((t - (DUR - 1.9)) / 0.5)
    if fl > 0:
        a = int(255 * (1 - abs(fl * 2 - 1)))
        im.alpha_composite(Image.new('RGBA', (W, H), ORANGE + (int(a * 0.5),)))
    return im.convert('RGB')

if __name__ == '__main__':
    import sys
    print({k: round(v, 1) for k, v in T.items()}, round(T_SUB, 1))
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_intro_{tt:05.1f}.png')
