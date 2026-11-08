from common import *
from widgets import *

words = words_of('devis')
DUR = D['devis']
def _rows(spec):
    out = []
    for lab, amt, key in spec:
        tw_ = find(words, key); t0 = tw_ - 0.2
        tr = find(words, 'environ', 0, tw_) + 0.9
        out.append((lab, amt, t0, tr))
    return out
GO_ROWS = _rows([('Fondation', 5400000, 'fondation'), ('Élévation RDC', 4000000, 'rez-de-chaussée'), ('Dalle', 7600000, 'dalle'), ('Élévation étage', 4500000, "l'étage"), ('Charpente et toiture', 6800000, 'charpente')])
FIN_ROWS = _rows([('Crépissage et antivols', 8300000, 'crépissage'), ('Portes et fenêtres', 6200000, 'portes'), ('Plomberie et électricité', 5200000, 'plomberie'), ('Plafond et peinture', 7300000, 'plafond'), ('Carrelage', 7600000, 'carrelage')])
GO = 28300000; FIN = 34600000; RMIN, RMAX = 57800000, 67800000
f = lambda p, n=0: find(words, p, n)
T_PAYS = f('pays'); T_TERR = f('terrain'); T_TECH = f('techniciens'); T_ENTRE = f('entre'); T_VOY = f('voyons'); T_GROS = f('gros', 0)
T_PLUS = f('poste'); T_TOT = f('total'); T_PASS = f('passons'); T_PESENT = f('pèsent'); T_MOIT = f('moitié'); T_ATT = f('attention')
T_SOL = f('sol'); T_QUAL = f('qualité'); T_MAT = f('matériaux', 1); T_VRAIS = f('vrais'); T_SELON = f('selon', 1); T_CAT = f('catalogue')
MAXV = 8300000
GO_END = T_PASS - 0.6; FIN_END = T_ATT - 0.3; CEND = T_VRAIS - 0.6
_bg = None

def fmt(n): return f'{int(n):,}'.replace(',', ' ')

def bg():
    global _bg
    if _bg is None:
        b = Image.new('RGBA', (W, H), LIGHT + (255,))
        lg = img('logo_green.png').copy(); lg.thumbnail((800, 520)); paste_alpha(b, lg, (W // 2 - 400, H // 2 - 200), 0.05)
        header(b, 'Devis estimatif · clé en main')
        _bg = b
    return _bg

def layer(): return Image.new('RGBA', (W, H), (0, 0, 0, 0))

def fade(ov, a):
    if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * clamp(a))))
    return ov

def row(base, i, lab, amt, t0, tr, t, col, y0, rh, alpha=1.0, shift=0, tag=None):
    k = e_out((t - t0) / 0.6)
    if k <= 0.01: return
    y = y0 + i * rh
    ov = layer(); od = ImageDraw.Draw(ov)
    x = 60 - shift
    od.text((x, y + rh // 2), lab, font=font(34), fill=DARK, anchor='lm')
    bx, bw = 560 - shift, 340
    od.rounded_rectangle((bx, y + rh // 2 - 28, bx + bw, y + rh // 2 + 28), 28, fill=(226, 232, 236, 255))
    kv = e_out((t - tr + 0.6) / 1.0)
    wv = max(36, int(bw * amt / MAXV * clamp(kv)))
    od.rounded_rectangle((bx, y + rh // 2 - 28, bx + wv, y + rh // 2 + 28), 28, fill=col + (255,))
    if kv > 0.02:
        od.text((bx + bw + 22, y + rh // 2), fmt(amt * clamp(kv)), font=font(38), fill=DARK, anchor='lm')
    if tag and t > tag[0]:
        ta = e_back((t - tag[0]) / 0.4)
        wl = int(tw(tag[1], 26) + 40)
        od.rounded_rectangle((bx + bw - wl, y + rh // 2 - 68, bx + bw, y + rh // 2 - 28), 20, fill=ORANGE + (int(255 * clamp(ta)),))
        od.text((bx + bw - wl // 2, y + rh // 2 - 48), tag[1], font=font(26), fill=WHITE, anchor='mm')
    base.alpha_composite(fade(ov, k * alpha))

def frame(t):
    base = bg().copy()
    # --- A : intro des variables + fourchette (0 -> 15)
    aA = 1 - e_io((t - 14.6) / 0.8)
    if aA > 0.01:
        ov = layer(); od = ImageDraw.Draw(ov)
        text(od, (620, 200), 'COMBIEN VA COÛTER CE DUPLEX ?', 48, GREEN, 'mm')
        for (ch, lab, tt, cx) in (('', 'Votre pays', T_PAYS, 480), ('', 'Votre terrain', T_TERR, 960), ('', 'Vos techniciens', T_TECH, 1440)):
            pass
        base.alpha_composite(fade(ov, aA))
        for (ch, lab, tt, cx) in (('', 'Votre pays', T_PAYS - 0.2, 200), ('', 'Votre terrain', T_TERR - 0.2, 590), ('', 'Vos techniciens', T_TECH - 0.2, 970)):
            tmp = layer(); pill_icon(tmp, (cx, 340), ch, lab, t, tt, GREEN, size=30); base.alpha_composite(fade(tmp, aA))
        p = e_back((t - T_ENTRE) / 0.5)
        if p > 0.02:
            off = int((1 - clamp(p, 0, 1)) * 60)
            ov = layer(); shadow_card(ov, (60, 440 + off, 1180, 890 + off), r=36); od = ImageDraw.Draw(ov)
            text(od, (620, 520 + off), 'ENTRE', 34, GREY, 'mm')
            text(od, (620, 630 + off), fmt(RMIN), 88, GREEN, 'mm')
            text(od, (620, 735 + off), 'et ' + fmt(RMAX), 88, GREEN, 'mm')
            text(od, (620, 835 + off), 'FCFA · clé en main', 44, ORANGE, 'mm')
            base.alpha_composite(fade(ov, clamp(p) * aA))
    # --- ruban fourchette (15 -> fin)
    rb = e_io((t - 14.9) / 0.7)
    if rb > 0.01:
        ov = layer(); od = ImageDraw.Draw(ov)
        od.rounded_rectangle((80, 128, 1840, 214), 43, fill=GREEN + (255,))
        od.text((960, 171), f'Fourchette : {fmt(RMIN)} à {fmt(RMAX)} FCFA · clé en main', font=font(40), fill=WHITE, anchor='mm')
        base.alpha_composite(fade(ov, rb))
    # --- B : gros œuvre
    gA = 1
    sh = 0
    if t > GO_END: sh = int(e_io((t - GO_END) / 0.7) * 120)
    for i, (lab, amt, t0, tr) in enumerate(GO_ROWS):
        tag = (T_PLUS - 0.4, 'PLUS GROS POSTE') if i == 2 else None
        row(base, i, lab, amt, t0, tr, t, GREEN, 285, 112, alpha=1 - e_io((t - GO_END) / 0.7), shift=sh, tag=tag)
    if t > T_GROS - 0.5 and t < GO_END + 0.9:
        pb = e_back((t - (T_GROS - 0.5)) / 0.4) * (1 - e_io((t - GO_END) / 0.7))
        ov = layer(); od = ImageDraw.Draw(ov)
        y = 620; x0 = 1236
        od.rounded_rectangle((x0, y, 1880, y + 210), 28, fill=GREEN + (255,))
        od.text((x0 + 322, y + 50), 'GROS ŒUVRE', font=font(36), fill=WHITE, anchor='mm')
        if t > T_TOT + 2:
            kk = e_out((t - (T_TOT + 2.0)) / 1.0)
            od.text((x0 + 322, y + 140), fmt(GO * kk), font=font(60), fill=WHITE, anchor='mm')
        base.alpha_composite(fade(ov, clamp(pb)))
    # --- B2 : finitions
    fA = 1
    for i, (lab, amt, t0, tr) in enumerate(FIN_ROWS):
        row(base, i, lab, amt, t0, tr, t, ORANGE, 285, 112, alpha=1 - e_io((t - FIN_END) / 0.7))
    if t > T_PASS - 0.3 and t < FIN_END + 0.3:
        pb = e_back((t - (T_PASS - 0.3)) / 0.4)
        ov = layer(); od = ImageDraw.Draw(ov)
        y = 620; x0 = 1236
        od.rounded_rectangle((x0, y, 1880, y + 210), 28, fill=ORANGE + (255,))
        od.text((x0 + 322, y + 50), 'FINITIONS', font=font(36), fill=WHITE, anchor='mm')
        if t > T_PESENT:
            kk = e_out((t - T_PESENT) / 1.0)
            od.text((x0 + 322, y + 140), fmt(FIN * kk), font=font(60), fill=WHITE, anchor='mm')
        base.alpha_composite(fade(ov, clamp(pb) * (1 - e_io((t - FIN_END) / 0.7))))
    # barre de proportion
    if t > T_MOIT - 0.8:
        a = e_out((t - (T_MOIT - 0.8)) / 0.5) * (1 - e_io((t - FIN_END) / 0.7))
        ov = layer(); od = ImageDraw.Draw(ov)
        pg = GO / (GO + FIN); x0, x1, y0, y1 = 60, 1180, 890, 970
        xm = x0 + (x1 - x0) * pg
        od.rounded_rectangle((x0, y0, x1, y1), 40, fill=ORANGE + (255,))
        od.rounded_rectangle((x0, y0, xm + 30, y1), 40, fill=GREEN + (255,))
        od.rectangle((xm - 10, y0, xm + 30, y1), fill=ORANGE + (255,)) if False else None
        od.text(((x0 + xm) / 2, 930), f'Gros œuvre {round(pg * 100)} %', font=font(28), fill=WHITE, anchor='mm')
        od.text(((xm + x1) / 2, 930), f'Finitions {round((1 - pg) * 100)} %', font=font(28), fill=WHITE, anchor='mm')
        base.alpha_composite(fade(ov, a))
    # --- C : montants indicatifs
    cA = e_io((t - (T_ATT - 0.2)) / 0.6) * (1 - e_io((t - CEND) / 0.6))
    if cA > 0.01:
        ov = layer(); od = ImageDraw.Draw(ov)
        rrect(od, (60, 300, 1180, 420), 60, fill=ORANGE + (255,))
        text(od, (620, 360), 'MONTANTS INDICATIFS', 60, WHITE, 'mm')
        base.alpha_composite(fade(ov, cA))
        for (ch, lab, tt, cx) in (('', 'Le type de sol', T_SOL - 0.3, 960), ('', 'La qualité des techniciens', T_QUAL - 0.3, 960), ('', 'Les matériaux', T_MAT - 0.3, 960)):
            pass
        for k, (ch, lab, tt) in enumerate((('', 'Le type de sol', T_SOL - 0.3), ('', 'La qualité des techniciens', T_QUAL - 0.3), ('', 'Les matériaux', T_MAT - 0.3))):
            tmp = layer(); pill_icon(tmp, (620, 540 + k * 140), ch, lab, t, tt, GREEN, size=40); base.alpha_composite(fade(tmp, cA))
    # --- D : vrais coûts -> catalogue
    dA = e_io((t - (T_VRAIS - 0.2)) / 0.6)
    if dA > 0.01:
        ov = layer(); shadow_card(ov, (60, 300, 1180, 860), r=40); od = ImageDraw.Draw(ov)
        text(od, (620, 390), 'Les vrais coûts de construction', 50, DARK, 'mm')
        pa = e_back((t - (T_SELON - 0.2)) / 0.4)
        if pa > 0.02: text(od, (620, 480), 'selon votre pays', 70, ORANGE, 'mm')
        ca = e_out((t - (T_CAT - 0.2)) / 0.5)
        if ca > 0.02:
            lg = img('logo_green.png').copy(); lg.thumbnail((360, 200))
            rrect(od, (110, 580, 1130, 800), 36, fill=GREEN + (int(255 * ca),))
            od.text((620, 650), 'Catalogue Premium WooPlans', font=font(54), fill=WHITE + (int(255 * ca),), anchor='mm')
            od.text((620, 735), 'Lien dans la description', font=font(36), fill=GOLD + (int(255 * ca),), anchor='mm')
        base.alpha_composite(fade(ov, dA))
    render_box(base, (1236, 235, 1880, 590), t, start=3)
    return base.convert('RGB')

if __name__ == '__main__':
    import sys
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_devis_{tt:05.1f}.png')
