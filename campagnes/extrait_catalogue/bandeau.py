"""Visuels de l'« Extrait du Catalogue Premium » (test du 17 nov. 2026) : les 4 visuels gagnants du guide, bandeau du
bas remplacé (« Extrait du Catalogue Premium · 5 maisons avec plan et devis · 1 900 FCFA · wooplans.com »).
Usage : python campagnes/extrait_catalogue/bandeau.py
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from wooplans.guardrails import check_copy  # noqa: E402

SRC = ROOT / "campagnes" / "guide_des_maisons" / "creas"
OUT = Path(__file__).resolve().parent / "creas"
FONT = ROOT / "youtube_plan" / "jobs" / "V3-017" / "assets" / "Poppins-Bold.ttf"
WHITE, GOLD, ORANGE = (255, 255, 255), (231, 195, 108), (240, 138, 46)

LINE1 = "Extrait du Catalogue Premium"
LINE2 = "5 maisons avec plan et devis"
PILL = "PDF · 1 900 FCFA"
URL = "wooplans.com"

# visuel du guide -> (nouveau nom, haut du bandeau à remplacer en px)
CREAS = {
    "crea-6-preferees-clients.jpg": ("extrait-1-preferees-clients.jpg", 1145),
    "crea-7-plus-demandees.jpg": ("extrait-2-plus-demandees.jpg", 1120),
    "crea-8-combien-coute.jpg": ("extrait-3-combien-coute.jpg", 1095),
    "crea-9-preferees-story-9x16.jpg": ("extrait-4-preferees-story-9x16.jpg", 1597),
}


def font(size):
    return ImageFont.truetype(str(FONT), size)


def fit(draw, text, size, max_w):
    while draw.textlength(text, font=font(size)) > max_w and size > 10:
        size -= 1
    return font(size)


def band(src: Path, dst: Path, top: int):
    im = Image.open(src).convert("RGB")
    w, h = im.size
    d = ImageDraw.Draw(im)
    bg = im.getpixel((6, top + 30))
    d.rectangle([0, top, w, h], fill=bg)
    avail = h - top
    big = avail > 300  # format Story : plus de place
    scale = 1.0
    while True:
        f1 = fit(d, LINE1, int((64 if big else 50) * scale), w - 80)
        f2 = fit(d, LINE2, int((54 if big else 40) * scale), w - 80)
        fp = font(int((64 if big else 50) * scale))
        fu = font(int((34 if big else 28) * scale))
        # hauteurs réelles (Poppins : la ligne fait environ 1,05 fois la taille depuis le haut des capitales)
        h1, h2, hu = f1.size * 1.08, f2.size * 1.12, fu.size * 1.1
        ph = fp.size + int((40 if big else 24) * scale)
        gap = int((22 if big else 10) * scale)
        total = h1 + h2 + gap + ph + gap + hu
        if total <= avail - 18 or scale < 0.5:
            break
        scale -= 0.04
    y = top + (avail - total) / 2
    d.text((w / 2, y), LINE1, font=f1, fill=WHITE, anchor="mt")
    y += h1
    d.text((w / 2, y), LINE2, font=f2, fill=GOLD, anchor="mt")
    y += h2 + gap
    pw = d.textlength(PILL, font=fp) + (120 if big else 100)
    d.rounded_rectangle([w / 2 - pw / 2, y, w / 2 + pw / 2, y + ph], radius=ph / 2, fill=ORANGE)
    d.text((w / 2, y + ph / 2), PILL, font=fp, fill=WHITE, anchor="mm")
    y += ph + gap
    d.text((w / 2, y), URL, font=fu, fill=WHITE, anchor="mt")
    im.save(dst, quality=92)


def main():
    problems = [p for t in (LINE1, LINE2, PILL) for p in check_copy(t, allowed_amounts=(1900,))]
    if problems:
        raise SystemExit(f"Texte refusé : {problems}")
    OUT.mkdir(parents=True, exist_ok=True)
    for src, (name, top) in CREAS.items():
        band(SRC / src, OUT / name, top)
        print(OUT / name)


if __name__ == "__main__":
    main()
