from common import *
from widgets import *
from seq_intro import kb
SRC = Image.open(A + 'R0.png').convert('RGB')
DUR = D['fin']
words = words_of('fin'); f = lambda p, n=0: find(words, p, n)
T_POUCE = f('pouce'); T_ABO = f('abonnez-vous'); T_AUTRE = f('regardez'); T_ICI = f('juste')

def fade_(ov, a):
    if a < 1: ov.putalpha(ov.getchannel('A').point(lambda v: int(v * clamp(a))))
    return ov

def frame(t):
    base = kb(SRC, t, DUR, 1.0, 1.06, (0.5, 0.5), (0.45, 0.5)).convert('RGBA')   # image lumineuse, aucun voile sombre
    d = ImageDraw.Draw(base)
    # logo sur pastille blanche
    lg = img('logo_green.png').copy(); lg.thumbnail((200, 100))
    rrect(d, (40, 30, 40 + lg.width + 40, 30 + lg.height + 30), 28, fill=WHITE + (235,))
    base.alpha_composite(lg, (60, 45))
    # phrase d'accroche
    pa = e_back((t - 0.2) / 0.4)
    if pa > 0.02:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        wl = int(tw('Voilà pour ce duplex !', 52) + 70)
        rrect(od, (60, 220, 60 + wl, 320), 50, fill=GREEN + (255,))
        od.text((60 + wl // 2, 270), 'Voilà pour ce duplex !', font=font(52), fill=WHITE, anchor='mm')
        base.alpha_composite(fade_(ov, clamp(pa) * (1 - e_io((t - (T_AUTRE - 0.3)) / 0.4))))
    # pouce + abonnement (côté gauche, court)
    aa = e_io((t - (T_POUCE - 0.4)) / 0.35) * (1 - e_io((t - (T_AUTRE - 0.5)) / 0.4))
    if aa > 0.01:
        tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0))
        p = e_back((t - (T_POUCE - 0.1)) / 0.35)
        if p > 0.02:
            td = ImageDraw.Draw(tmp); r = int(95 * clamp(p, 0, 1.1)); cx, cy = 190, 640
            td.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(24, 119, 242, 255), outline=WHITE + (255,), width=6)
            icon(td, (cx, cy), '', int(95 * clamp(p, 0, 1.1)), WHITE)
        base.alpha_composite(fade_(tmp, aa))
        tmp = Image.new('RGBA', (W, H), (0, 0, 0, 0)); subscribe_btn(tmp, t, T_ABO - 0.2, T_AUTRE - 0.5, 600, 640, click_at=0.8)
        base.alpha_composite(fade_(tmp, aa))
    # autre plan : cadre vide pour l'écran de fin YouTube
    za = e_io((t - (T_AUTRE - 0.25)) / 0.35)
    if za > 0.01:
        ov = Image.new('RGBA', (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
        wl = int(tw('Regardez cet autre plan', 56) + 70)
        rrect(od, (1410 - wl // 2, 190, 1410 + wl // 2, 280), 45, fill=ORANGE + (255,))
        od.text((1410, 235), 'Regardez cet autre plan', font=font(56), fill=WHITE, anchor='mm')
        zx0, zy0, zx1, zy1 = 1030, 320, 1810, 760
        pulse = 0.5 + 0.5 * math.sin(t * 5)
        a_b = int(170 + 85 * pulse) if t > T_ICI else 170
        od.rounded_rectangle((zx0, zy0, zx1, zy1), 30, fill=(255, 255, 255, 18), outline=WHITE + (a_b,), width=8)
        if t > T_ICI - 0.2:
            ax = zx0 - 140 + int(22 * math.sin(t * 6))
            od.polygon([(ax, 540 - 44), (ax + 76, 540), (ax, 540 + 44)], fill=ORANGE + (255,), outline=WHITE + (255,))
            od.rectangle((ax - 110, 540 - 16, ax + 8, 540 + 16), fill=ORANGE + (255,), outline=WHITE + (255,))
            rrect(od, (1410 - 130, 800, 1410 + 130, 880), 40, fill=WHITE + (240,))
            od.text((1410, 840), 'juste ici', font=font(52), fill=ORANGE, anchor='mm')
        base.alpha_composite(fade_(ov, za))
    return base.convert('RGB')

if __name__ == '__main__':
    import sys
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_fin_{tt:05.1f}.png')
