"""Remplace les étiquettes d'un plan 2D : efface le texte sombre dans une fenêtre autour de chaque étiquette
(fond = médiane des pixels clairs de la fenêtre) puis écrit le libellé français en Poppins Bold.

  relabel(img, [(cx, cy, demi_largeur, demi_hauteur, ["LIGNE 1", ...], {"rot": 90, "size": 18}), ...], couleur)
"""
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT = str(Path(__file__).resolve().parents[1] / "fonts" / "Poppins-Bold.ttf")


def erase(im, cx, cy, hw, hh, dark=120):
    a = np.asarray(im).astype(int)
    x0, y0, x1, y1 = cx - hw, cy - hh, cx + hw, cy + hh
    win = a[y0:y1, x0:x1]
    lum = win.mean(-1)
    mask = lum < dark
    if not mask.any():
        return None
    ys, xs = np.where(mask)
    bx0, by0, bx1, by1 = x0 + xs.min() - 3, y0 + ys.min() - 3, x0 + xs.max() + 4, y0 + ys.max() + 4
    light = win[lum > 200]
    fill = tuple(int(v) for v in (np.median(light, axis=0) if len(light) else (255, 255, 255)))
    ImageDraw.Draw(im).rectangle([bx0, by0, bx1, by1], fill=fill)
    return (bx0, by0, bx1, by1), fill


def write(im, cx, cy, lines, color, size=18, rot=0, maxw=None):
    f = ImageFont.truetype(FONT, size)
    d = ImageDraw.Draw(im)
    if maxw:
        while size > 10 and max(d.textlength(t, font=f) for t in lines) > maxw:
            size -= 1
            f = ImageFont.truetype(FONT, size)
    lh = int(size * 1.15)
    w = int(max(d.textlength(t, font=f) for t in lines)) + 8
    h = lh * len(lines) + 6
    lay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    for i, t in enumerate(lines):
        ld.text((w // 2, 3 + lh * i + lh // 2), t, font=f, fill=color, anchor="mm")
    if rot:
        lay = lay.rotate(rot, expand=True)
    im.paste(lay, (cx - lay.width // 2, cy - lay.height // 2), lay)


def relabel(im, labels, color):
    im = im.convert("RGB")
    for cx, cy, hw, hh, lines, opt in labels:
        erase(im, cx, cy, hw, hh, opt.get("dark", 120))
        write(im, cx, cy, lines, color, opt.get("size", 18), opt.get("rot", 0), opt.get("maxw"))
    return im
