from common import *
from widgets import *
P1 = Image.open(A + 'rdc3d.png').convert('RGB'); P2 = Image.open(A + 'et3d.png').convert('RGB')
words = words_of('invit'); TOKS = caption_tokens(words)
DUR = D['invit']
TCOM = find(words, 'commentaire'); TSHARE = find(words, r'partagez-lui'); TAIDE = find(words, 'aide')
_bg = None

def bg():
    global _bg
    if _bg is None:
        b = Image.new('RGBA', (W, H), LIGHT + (255,))
        lg = img('logo_green.png').copy(); lg.thumbnail((900, 600)); paste_alpha(b, lg, (W // 2 - lg.width // 2, H // 2 - lg.height // 2 + 40), 0.06)
        header(b, 'Votre avis compte')
        _bg = b
    return _bg

def frame(t):
    base = bg().copy()
    # plan entier à gauche
    s = lerp(0.96, 1.0, e_out(t / 0.6))
    for k, (PL, lab) in enumerate(((P1, 'RDC'), (P2, 'ÉTAGE'))):
        pw = int(470 * s); ph = int(pw * PL.height / PL.width)
        x0, y0 = 70 + k * 500, 150 + (800 - ph) // 2
        shadow_card(base, (x0 - 14, y0 - 14, x0 + pw + 14, y0 + ph + 14), r=26)
        base.alpha_composite(PL.resize((pw, ph), Image.LANCZOS).convert('RGBA'), (x0, y0))
        dd = ImageDraw.Draw(base); rrect(dd, (x0, y0 - 64, x0 + 150, y0 - 14), 25, fill=GREEN); text(dd, (x0 + 75, y0 - 39), lab, 28, WHITE, 'mm')
    # bulles de droite
    d = ImageDraw.Draw(base)
    p1 = e_back((t - TCOM + 0.3) / 0.45)
    if p1 > 0.02:
        pill_icon(base, (1470, 330), '', 'Votre avis en commentaire', t, TCOM - 0.3, ORANGE, size=36)
        d = ImageDraw.Draw(base)
        text(d, (1470, 430), 'Que changeriez-vous dans ce plan ?', 34, GREY, 'mm')
    p2 = e_back((t - TSHARE + 0.3) / 0.45)
    if p2 > 0.02:
        pill_icon(base, (1470, 560), '', 'Partagez à un proche', t, TSHARE - 0.3, GREEN, size=36)
        d = ImageDraw.Draw(base)
        text(d, (1470, 660), 'Il prépare sa construction ?', 34, GREY, 'mm')
    subscribe_btn(base, t, TAIDE - 0.2, 1e9, 1470, 820, click_at=1.1)
    draw_caption(base, TOKS, t)
    return base.convert('RGB')

if __name__ == '__main__':
    import sys
    for tt in [float(x) for x in sys.argv[1:]]:
        frame(tt).save(OUTDIR + f'/test_invit_{tt:05.1f}.png')
