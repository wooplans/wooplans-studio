"""Visuels de la campagne de reciblage du Catalogue Premium (21 nov. 2026, visiteurs 60 j + Page 90 j).

Bases générées par Poyo (gpt-image-2.6-fixed, 1K, rendus réels du site en référence) dans le style des pubs gagnantes
de l'extrait ; ce script incruste le logo officiel en haut et le bandeau du bas (offre, prix, wooplans.com), et floute
le tableau de devis du visuel 2 (montants inventés par le générateur, et en euros).
Budgets affichés : fiches du site (D1, 20 nov. 2026). Prix : 29 000 FCFA, 60 000 barré (prix de référence du site).
Usage : python campagnes/reciblage_catalogue/visuels.py <dossier des PNG Poyo>
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from wooplans.guardrails import check_copy  # noqa: E402

OUT = Path(__file__).resolve().parent / "creas"
FONT = ROOT / "youtube_plan" / "jobs" / "V3-017" / "assets" / "Poppins-Bold.ttf"
LOGO = ROOT / "assets" / "brand" / "logo_white_horizontal.png"  # logo du site, horizontal
WHITE, GOLD, ORANGE = (255, 255, 255), (231, 195, 108), (240, 138, 46)
W, H = 1080, 1350

LINE1 = "Catalogue Premium · 100 villas et duplex"
LINE2 = "avec plan coté et devis poste par poste"
BEFORE, PRICE = "60 000", "29 000 FCFA"
URL = "wooplans.com"

LOGO_H = 70  # bande du logo en haut
BAND_TOP = 1128  # haut du bandeau du bas

# base Poyo -> (nom, zone à flouter en px de la base redimensionnée en 1080 x 1350, ou None)
CREAS = {
    "EH7IWWCE7TIO362R.png": ("catalogue-1-plans-et-devis.jpg", None),
    "831TILISP0V1NAMM.png": ("catalogue-2-plan-et-devis.jpg", (690, 790, 1000, 1085)),
    "NHNEF5TQXMS9JRLY.png": ("catalogue-3-quelle-maison.jpg", None),
}


def font(size):
    return ImageFont.truetype(str(FONT), size)


def fit(d, text, size, max_w):
    while d.textlength(text, font=font(size)) > max_w and size > 10:
        size -= 1
    return font(size)


def content_rows(im, bg):
    """Première et dernière ligne qui ne sont pas du fond (le générateur laisse des marges vides)."""
    px = im.load()
    rows = [y for y in range(im.height) if any(sum(abs(a - b) for a, b in zip(px[x, y], bg)) > 60 for x in range(0, im.width, 6))]
    return rows[0], rows[-1]


def finish(src: Path, dst: Path, blur):
    base = Image.open(src).convert("RGB").resize((W, H), Image.LANCZOS)
    if blur:
        base.paste(base.crop(blur).filter(ImageFilter.GaussianBlur(9)), blur[:2])
    bg = base.getpixel((6, H - 6))
    first, last = content_rows(base, bg)
    content = base.crop((0, max(first - 12, 0), W, min(last + 12, H)))
    # le contenu (titre + maisons) est ramené entre la bande du logo et le bandeau du bas
    room = BAND_TOP - LOGO_H - 8
    if content.height > room:
        content = content.resize((int(W * room / content.height), room), Image.LANCZOS)
    im = Image.new("RGB", (W, H), bg)
    im.paste(content, ((W - content.width) // 2, LOGO_H + 4))
    d = ImageDraw.Draw(im)
    logo = Image.open(LOGO).convert("RGBA")
    lw = 190
    logo = logo.resize((lw, int(logo.height * lw / logo.width)), Image.LANCZOS)
    lh = min(logo.height, LOGO_H - 16)
    logo = logo.resize((int(logo.width * lh / logo.height), lh), Image.LANCZOS)
    im.paste(logo, ((W - logo.width) // 2, (LOGO_H - lh) // 2 + 4), logo)
    # bandeau du bas
    f1, f2 = fit(d, LINE1, 44, W - 80), fit(d, LINE2, 34, W - 80)
    fb, fp, fu = font(34), font(48), font(26)
    y = BAND_TOP + 10
    d.text((W / 2, y), LINE1, font=f1, fill=WHITE, anchor="mt")
    y += f1.size * 1.2
    d.text((W / 2, y), LINE2, font=f2, fill=GOLD, anchor="mt")
    y += f2.size * 1.45
    # pilule : 60 000 barré + 29 000 FCFA
    bw, pw = d.textlength(BEFORE, font=fb), d.textlength(PRICE, font=fp)
    ph = fp.size + 22
    total = bw + 22 + pw + 84
    x0 = W / 2 - total / 2
    d.rounded_rectangle([x0, y, x0 + total, y + ph], radius=ph / 2, fill=ORANGE)
    bx = x0 + 42
    d.text((bx, y + ph / 2), BEFORE, font=fb, fill=(255, 228, 196), anchor="lm")
    d.line([bx - 2, y + ph / 2 + 1, bx + bw + 2, y + ph / 2 + 1], fill=WHITE, width=4)
    d.text((bx + bw + 22, y + ph / 2), PRICE, font=fp, fill=WHITE, anchor="lm")
    y += ph + 10
    d.text((W / 2, y), URL, font=fu, fill=WHITE, anchor="mt")
    im.save(dst, quality=92)


def main():
    src_dir = Path(sys.argv[1])
    problems = [p for t in (LINE1, LINE2, f"{BEFORE} FCFA", PRICE) for p in check_copy(t, allowed_amounts=(29000, 60000))]
    if problems:
        raise SystemExit(f"Texte refusé : {problems}")
    OUT.mkdir(parents=True, exist_ok=True)
    for src, (name, blur) in CREAS.items():
        finish(src_dir / src, OUT / name, blur)
        print(OUT / name)


if __name__ == "__main__":
    main()
