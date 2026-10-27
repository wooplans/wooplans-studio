from common import *
from widgets import *
PLAN = Image.open(A + 'rdc3d.png').convert('RGB')
words = words_of('chiffres'); TOKS = caption_tokens(words)
DUR = D['chiffres']
T149 = find(words, 'trois'); TNIV = find(words, 'niveaux'); TSEIZE = find(words, 'quinze'); TTREIZE = find(words, 'treize'); TENTRE = find(words, 'maintenant') - 0.5
CY0, CY1 = 135, 625
_bg = None

def bg():
    global _bg
    if _bg is None:
        b = Image.new('RGBA', (W, H), LIGHT + (255,))
        lg = img('logo_green.png').copy(); lg.thumbnail((900, 600)); paste_alpha(b, lg, (W // 2 - lg.width // 2, H // 2 - lg.height // 2 + 40), 0.06)
        header(b, 'Le duplex en chiffres')
        _bg = b
    return _bg

def card(base, box, p, r=30):
    x0, y0, x1, y1 = box
    off = int((1 - clamp(p)) * 60) + 120
    shadow_card(base, (x0, y0 + off, x1, y1 + off), r=r)
    return off

def frame(t):
    base = bg().copy(); d = ImageDraw.Draw(base)
    ex = e_io((t - (TENTRE + 0.5)) / 0.9)  # sortie
    # carte A : 149 m²
    pa = e_back((t - (T149 - 0.5)) / 0.5)
    if pa > 0.02:
        box = (60, CY0, 400, CY1); off = card(base, box, pa); d = ImageDraw.Draw(base)
        text(d, (230, 205 + off), 'SURFACE TOTALE', 26, GREY, 'mm')
        s = int(150 * (0.7 + 0.3 * clamp(pa, 0, 1.1)))
        text(d, (230, 350 + off), '314', s, ORANGE, 'mm')
        text(d, (230, 465 + off), 'm²', 70, ORANGE, 'mm')
        text(d, (230, 540 + off), 'terrasses et', 30, DARK, 'mm')
        text(d, (230, 578 + off), 'garage compris', 30, DARK, 'mm')
    # carte B : un seul niveau
    pb = e_back((t - (TNIV - 1.2)) / 0.5)
    if pb > 0.02:
        box = (420, CY0, 780, CY1); off = card(base, box, pb); d = ImageDraw.Draw(base)
        text(d, (600, 205 + off), 'NIVEAUX', 26, GREY, 'mm')
        hx, hy = 600, 360 + off
        d.polygon([(hx - 160, hy - 95), (hx - 90, hy - 165), (hx + 90, hy - 165), (hx + 160, hy - 95)], fill=DARK)
        d.rectangle((hx - 140, hy - 95, hx + 140, hy - 15), fill=GREEN); d.rectangle((hx - 140, hy - 15, hx + 140, hy + 65), fill=(34, 120, 118))
        d.line((hx - 140, hy - 15, hx + 140, hy - 15), fill=WHITE, width=4)
        for xx in (-100, -30, 60): d.rectangle((hx + xx, hy - 78, hx + xx + 45, hy - 38), fill=WHITE)
        d.rectangle((hx - 25, hy + 10, hx + 25, hy + 65), fill=ORANGE)
        d.line((hx - 165, hy + 65, hx + 165, hy + 65), fill=GREY, width=4)
        text(d, (600, 510 + off), '2 NIVEAUX', 46, DARK, 'mm')
        text(d, (600, 568 + off), 'RDC + étage', 32, GREY, 'mm')
    # carte C : plan + cotes
    pc = e_back((t - (TSEIZE - 1.0)) / 0.5)
    if pc > 0.02:
        box = (800, CY0, 1180, CY1); off = card(base, box, pc); d = ImageDraw.Draw(base)
        text(d, (990, 190 + off), "EMPRISE AU SOL", 26, GREY, 'mm')
        pw = 270; ph = int(pw * PLAN.height / PLAN.width)
        im = PLAN.resize((pw, ph), Image.LANCZOS).convert('RGBA')
        px0, py0 = 825, 250 + off
        base.alpha_composite(im, (px0, py0))
        # cote largeur
        wa = e_out((t - TSEIZE + 0.1) / 0.7)
        yb = py0 + ph + 34
        if wa > 0:
            xe = px0 + int(pw * wa)
            d.line((px0, yb, xe, yb), fill=ORANGE, width=6)
            d.line((px0, yb - 14, px0, yb + 14), fill=ORANGE, width=6); d.line((xe, yb - 14, xe, yb + 14), fill=ORANGE, width=6)
            if wa >= 0.99: text(d, (px0 + pw // 2, yb + 52), '15,55 m', 40, ORANGE, 'mm')
        ha = e_out((t - TTREIZE + 0.1) / 0.7)
        xb = px0 + pw + 36
        if ha > 0:
            ye = py0 + int(ph * ha)
            d.line((xb, py0, xb, ye), fill=GREEN, width=6)
            d.line((xb - 14, py0, xb + 14, py0), fill=GREEN, width=6); d.line((xb - 14, ye, xb + 14, ye), fill=GREEN, width=6)
            if ha >= 0.99:
                tx = Image.new('RGBA', (300, 80), (0, 0, 0, 0)); ImageDraw.Draw(tx).text((150, 40), '13,80 m', font=font(36), fill=GREEN, anchor='mm')
                tx = tx.rotate(-90, expand=True); base.alpha_composite(tx, (xb + 6, py0 + ph // 2 - 150))
    render_box(base, (1236, 190, 1880, 800), t, start=0, pan=0.04)
    if ex > 0:
        base = Image.blend(base.convert('RGB'), Image.new('RGB', (W, H), WHITE), ex * 0.9).convert('RGBA')
    draw_caption(base, TOKS, t)
    return base.convert('RGB')

if __name__ == '__main__':
    import sys
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_chiffres_{tt:05.1f}.png')
