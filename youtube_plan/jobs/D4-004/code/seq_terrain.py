from common import *

words = words_of('terrain')
DUR = D['terrain']
S = 31.0
PLW, PLH = 18.55 * S, 20.80 * S           # terrain
HW, HH = 15.55 * S, 13.80 * S             # emprise
PLX = 300; PLY = 190
HX = PLX + 1.5 * S; HY = PLY + 2.0 * S
ROAD_Y = PLY + PLH + 3; ROAD_H = 3 * S
f = lambda p, n=0: find(words, p, n)
T_MAIS = f('maison'); T_SEIZE = f('quinze'); T_TREIZE = f('treize'); T_AUTOUR = f('autour')
T_COTE = f('côté'); T_150 = f('comptez'); T_AVANT = f("l'avant"); T_CINQ = f('cinq'); T_ARR = f("l'arrière"); T_DEUX = f('deux')
T_DIX = f('dix-huit'); T_VINGT = f('vingt'); T_C1 = f('cents', 0); T_C2 = T_C1
T_ROUTE = f('route', 0); T_ROUTE2 = f('route', 1); T_ENTREE = f("l'entrée", 1); T_CONSEIL = f('conseil'); T_LARG = f('largeur'); T_ETROIT = f('étroit'); T_REP = f('repères')
def dash_rect(d, box, color, width=4, dash=16, gap=10):
    x0, y0, x1, y1 = box
    def hl(y, xa, xb):
        x = xa
        while x < xb:
            d.line((x, y, min(x + dash, xb), y), fill=color, width=width); x += dash + gap
    def vl(x, ya, yb):
        y = ya
        while y < yb:
            d.line((x, y, x, min(y + dash, yb)), fill=color, width=width); y += dash + gap
    hl(y0, x0, x1); hl(y1, x0, x1); vl(x0, y0, y1); vl(x1, y0, y1)


def dim_h(d, x0, x1, y, label, k, color=DARK, sz=34):
    if k <= 0: return
    xe = lerp(x0, x1, e_out(k))
    d.line((x0, y, xe, y), fill=color, width=4)
    for xx in (x0, xe):
        d.line((xx, y - 14, xx, y + 14), fill=color, width=4)
    if k > 0.9:
        wl = tw(label, sz) + 30
        xm = (x0 + x1) / 2
        rrect(d, (xm - wl / 2, y - 24, xm + wl / 2, y + 24), 24, fill=WHITE, outline=color, width=3)
        text(d, (xm, y), label, sz, color, 'mm')


def dim_v(d, x, y0, y1, label, k, color=DARK, sz=34):
    if k <= 0: return
    ye = lerp(y0, y1, e_out(k))
    d.line((x, y0, x, ye), fill=color, width=4)
    for yy in (y0, ye):
        d.line((x - 14, yy, x + 14, yy), fill=color, width=4)
    if k > 0.9:
        wl = tw(label, sz) + 30
        ym = (y0 + y1) / 2
        rrect(d, (x - wl / 2, ym - 24, x + wl / 2, ym + 24), 24, fill=WHITE, outline=color, width=3)
        text(d, (x, ym), label, sz, color, 'mm')


def card(base, y, label, value, t, t0, accent=GREEN, h=112, vs=44):
    p = e_back((t - t0) / 0.4)
    if p <= 0.02: return
    off = int((1 - clamp(p, 0, 1)) * 60)
    ov = Image.new('RGBA', (W, H), (0, 0, 0, 0))
    shadow_card(ov, (1236, y + off, 1880, y + h + off), r=24)
    d = ImageDraw.Draw(ov)
    d.rounded_rectangle((1236, y + off, 1252, y + h + off), 8, fill=accent)
    text(d, (1280, y + off + 28), label, 22, GREY, 'lm')
    text(d, (1280, y + off + h - 38), value, vs, DARK if accent == GREEN else accent, 'lm')
    a = clamp(p)
    if a < 1:
        ov.putalpha(ov.getchannel('A').point(lambda v: int(v * a)))
    base.alpha_composite(ov)


def pill(d, xy, label, sz=28, fill=WHITE, color=DARK, outline=None):
    wl = tw(label, sz) + 30
    rrect(d, (xy[0] - wl / 2, xy[1] - 24, xy[0] + wl / 2, xy[1] + 24), 24, fill=fill, outline=outline or color, width=3)
    text(d, xy, label, sz, color, 'mm')


def frame(t):
    base = Image.new('RGBA', (W, H), LIGHT + (255,))
    lg = img('logo_green.png').copy(); lg.thumbnail((800, 520)); paste_alpha(base, lg, (W // 2 - 400, H // 2 - 200), 0.05)
    header(base, 'Le terrain à prévoir')
    d = ImageDraw.Draw(base)
    # route
    kr = e_out((t - T_ROUTE) / 0.8)
    if kr > 0:
        ry = ROAD_Y + (1 - kr) * 100
        d.rectangle((PLX - 170, ry, PLX + PLW + 170, ry + ROAD_H), fill=(75, 85, 99))
        xx = PLX - 150
        while xx < PLX + PLW + 150:
            d.rectangle((xx, ry + ROAD_H / 2 - 4, xx + 50, ry + ROAD_H / 2 + 4), fill=(229, 231, 235)); xx += 100
        text(d, (PLX + PLW + 120, ry + ROAD_H / 2), 'ROUTE', 28, WHITE, 'rm')
    # terrain qui se déploie autour de la maison
    kt = e_io((t - T_AUTOUR) / 1.3)
    if t >= T_AUTOUR - 0.02:
        x0 = lerp(HX, PLX, kt); y0 = lerp(HY, PLY, kt); x1 = lerp(HX + HW, PLX + PLW, kt); y1 = lerp(HY + HH, PLY + PLH, kt)
        d.rectangle((x0, y0, x1, y1), fill=(226, 240, 222))
        dash_rect(d, (x0, y0, x1, y1), GREEN, 5)
    # bandes de marges
    def band(box, t0, a_max=110):
        k = clamp((t - t0) / 0.5)
        if k <= 0: return 0
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rectangle(box, fill=ORANGE + (int(a_max * k),)); base.alpha_composite(ov); return k
    k1 = band((PLX, PLY + 2 * S, HX, HY + HH), T_COTE)
    k2 = band((HX + HW, PLY + 2 * S, PLX + PLW, HY + HH), T_COTE)
    k3 = band((PLX, HY + HH, PLX + PLW, PLY + PLH), T_AVANT)
    k4 = band((PLX, PLY, PLX + PLW, HY), T_ARR)
    d = ImageDraw.Draw(base)
    # maison
    kh = clamp((t - (T_MAIS - 0.3)) / 1.0)
    if kh > 0:
        a = int(255 * e_out(kh))
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.rectangle((HX, HY, HX + HW, HY + HH), fill=(255, 255, 255, a), outline=DARK + (a,), width=10)
        od.text((HX + HW * 0.30, HY + HH / 2 + 20), 'DUPLEX D4-004', font=font(28), fill=GREEN + (a,), anchor='mm')
        od.text((HX + HW * 0.30, HY + HH / 2 + 54), '314 m² · 4 chambres', font=font(20), fill=GREY + (a,), anchor='mm')
        base.alpha_composite(ov); d = ImageDraw.Draw(base)
    # cotes maison (dans la maison)
    dim_h(d, HX + 40, HX + HW - 40, HY + 60, '15,55 m', clamp((t - T_SEIZE) / 0.8), GREEN)
    dim_v(d, HX + HW - 60, HY + 100, HY + HH - 40, '13,80 m', clamp((t - T_TREIZE) / 0.8), GREEN)
    # étiquettes de marges
    if k1 > 0.9 and t > T_150 - 0.5: pill(d, (PLX + 25, HY + HH * 0.25), '1,50 m', 26, ORANGE, WHITE)
    if k2 > 0.9 and t > T_150 - 0.5: pill(d, (PLX + PLW - 25, HY + HH * 0.25), '1,50 m', 26, ORANGE, WHITE)
    if k3 > 0.9:
        if t > T_CINQ - 0.3:
            pill(d, (PLX + PLW - 45, HY + HH + 102), '5 m', 30, ORANGE, WHITE)
        if t > T_AVANT + 3.4:
            text(d, (PLX + 125, HY + HH + 60), 'COUR · ACCÈS', 24, ORANGE, 'mm'); text(d, (PLX + 125, HY + HH + 92), 'STATIONNEMENT', 24, ORANGE, 'mm')
    if k4 > 0.9 and t > T_DEUX - 0.3: pill(d, (PLX + PLW / 2, PLY + 33), '2 m', 26, ORANGE, WHITE)
    # cotes terrain
    dim_h(d, PLX, PLX + PLW, PLY - 40, '18,55 m', clamp((t - T_DIX) / 0.8), ORANGE)
    dim_v(d, PLX - 56, PLY, PLY + PLH, '20,80 m', clamp((t - T_VINGT) / 0.8), ORANGE)
    # entrée + vue des rendus
    ke = e_out((t - T_ROUTE2) / 0.6)
    if ke > 0:
        cx = HX + HW / 2
        y_from = ROAD_Y + 20; y_to = HY + HH + 14
        yy = lerp(y_from, y_to, ke)
        d.line((cx, y_from, cx, yy + 30), fill=DARK, width=10)
        d.polygon([(cx, yy), (cx - 26, yy + 40), (cx + 26, yy + 40)], fill=DARK)
        if t > T_ENTREE - 0.3: text(d, (cx + 40, (y_from + y_to) / 2 - 14), 'ENTRÉE', 32, DARK, 'lm')
        ex = cx - 260; ey = ROAD_Y + ROAD_H / 2 + 4
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        od.polygon([(ex, ey - 8), (cx - 150, HY + HH + 6), (cx + 10, HY + HH + 6)], fill=GOLD + (95,))
        base.alpha_composite(ov); d = ImageDraw.Draw(base)
        d.ellipse((ex - 46, ey - 26, ex + 46, ey + 26), fill=WHITE, outline=DARK, width=5)
        d.ellipse((ex - 14, ey - 14, ex + 14, ey + 14), fill=GREEN)
        d.ellipse((ex - 4, ey - 12, ex + 4, ey - 4), fill=WHITE)
    # terrain trop étroit : mini schéma
    if t >= T_ETROIT - 0.4 and t < T_REP + 0.2:
        a = e_out((t - T_ETROIT + 0.4) / 0.4) * clamp((T_REP + 0.2 - t) / 0.4)
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        m = 9.0; gx, gy = 1010, 250; gw, gh = 11.0 * m, 36.4 * m
        od.rounded_rectangle((gx - 60, gy - 70, gx + 205, gy + gh + 90), 22, fill=WHITE + (int(235 * a),))
        od.rectangle((gx, gy, gx + gw, gy + gh), fill=(226, 240, 222, int(255 * a)), outline=GREEN + (int(255 * a),), width=4)
        hx0 = gx + gw / 2 - 15.55 * m / 2
        od.rectangle((hx0, gy + 40, hx0 + 15.55 * m, gy + 40 + 13.80 * m), fill=(255, 255, 255, int(255 * a)), outline=(220, 38, 38, int(255 * a)), width=5)
        od.text((gx + 72, gy - 36), 'Même surface…', font=font(22), fill=DARK + (int(255 * a),), anchor='mm')
        od.text((gx + 72, gy + gh + 40), 'mais trop étroit', font=font(22), fill=(220, 38, 38, int(255 * a)), anchor='mm')
        base.alpha_composite(ov); d = ImageDraw.Draw(base)
    # cartes à droite
    card(base, 128, 'EMPRISE AU SOL DE LA MAISON', '15,55 × 13,80 m', t, T_SEIZE - 0.5, GREEN)
    card(base, 254, 'MARGES À PRÉVOIR', 'côtés 1,5 · avant 5 · arrière 2 m', t, T_150, ORANGE, vs=32)
    card(base, 380, 'TERRAIN À PRÉVOIR', '18,55 × 20,80 m', t, T_DIX, ORANGE)
    card(base, 506, 'TERRAIN MINIMUM · arrondi à 50 m²', '400 m²', t, T_C1 - 0.2, ORANGE, h=130, vs=64)
    render_box(base, (1236, 660, 1880, 900), t, start=2)
    if t > T_CONSEIL:
        a = e_out((t - T_CONSEIL) / 0.5)
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        rrect(od, (1236, 915, 1880, 1000), 26, fill=GREEN + (int(255 * a),))
        msg = 'Vérifiez la surface ET la largeur' if t < T_REP else 'Vous savez quoi chercher'
        od.text((1558, 958), msg, font=font(32), fill=WHITE + (int(255 * a),), anchor='mm')
        base.alpha_composite(ov)
    d = ImageDraw.Draw(base)
    text(d, (W // 2 + 40, 1045), 'Schéma indicatif · marges recommandées', 24, GREY, 'mm')
    return base.convert('RGB')


if __name__ == '__main__':
    import sys
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_terrain_{tt:05.1f}.png')
