"""Visuels publicitaires 4:5 (1080×1350) : rendu du modèle + chambres, douches, surface, prix du plan et devis, CTA.

  python tools/make_ad_creatives.py creatives/top7 [--price 39000]   # lit spec.json, écrit <code>_4x5.jpg + apercu.jpg
  --price : variante dont SEUL le montant change (fichiers suffixés _<montant>)
  --no-price : variante sans prix (bouton « TÉLÉCHARGER PLAN ET DEVIS »), fichiers suffixés _sansprix

Règles : textes passés dans check_copy (prix 14 900 FCFA autorisé, jamais d'urgence) ; rendus publics déjà filigranés
(jamais les originaux propres) ; adresse affichée : wooplans.com. Aucun envoi vers Meta : l'accord de Tao vient d'abord.
"""
import json
import sys
from pathlib import Path

import requests

from PIL import Image, ImageDraw, ImageFont, ImageOps

from wooplans.guardrails import check_copy
from wooplans.settings import ROOT

W, H = 1080, 1350
FONT = ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf"
TEAL_D, TEAL, GOLD, ORANGE, WHITE, SOFT = "#0A3A39", "#0F5B59", "#F6B73C", "#F59A23", "#FFFFFF", "#CFE6E3"
BOTTOM = 520          # hauteur du bloc bas (stats, prix, CTA, adresse)
TOP_MIN = 150


def font(size: int):
    return ImageFont.truetype(str(FONT), size)


def gradient(h: int) -> Image.Image:
    g = Image.new("RGB", (W, h))
    d = ImageDraw.Draw(g)
    a, b = tuple(int(TEAL_D[i:i + 2], 16) for i in (1, 3, 5)), tuple(int(TEAL[i:i + 2], 16) for i in (1, 3, 5))
    for y in range(h):
        t = y / max(1, h - 1)
        d.line([(0, y), (W, y)], fill=tuple(round(a[k] + (b[k] - a[k]) * t) for k in range(3)))
    return g


def centered(d, xy_center, text, f, fill):
    cx, cy = xy_center
    d.text((cx, cy), text, font=f, fill=fill, anchor="mm")


CTA_NO_PRICE = "TÉLÉCHARGER PLAN ET DEVIS"
SUBLINE_NO_PRICE = "Plan coté + devis détaillé du modèle"


def lines_for(p: dict, price: int) -> list:
    ch = f"{p['bedrooms']} chambres"
    dou = f"{p['bathrooms']} douches"
    if not price:  # variante sans prix : le prix est dans le texte de la pub et sur la fiche, selon le pays
        return [p["name"].upper(), ch, dou, f"{p['surface']} m²", SUBLINE_NO_PRICE, CTA_NO_PRICE, "wooplans.com"]
    return [p["name"].upper(), ch, dou, f"{p['surface']} m²", "Plan + devis du modèle", f"{price:,}".replace(",", " ") + " FCFA",
            "TÉLÉCHARGER MAINTENANT", "wooplans.com"]


def make(p: dict, root: Path, price: int, suffix: str = "") -> Path:
    problems = check_copy(" | ".join(lines_for(p, price)), allowed_amounts=[price])
    if problems:
        raise SystemExit(f"{p['code']} : {problems}")
    src = root / p["render"]
    if not src.is_file():                           # les images ne sont pas dans git : on retélécharge le rendu public
        src.parent.mkdir(parents=True, exist_ok=True)
        r = requests.get(p["url"], headers={"User-Agent": "Mozilla/5.0 (compatible; WooPlansStudio/1.0)"}, timeout=60)
        r.raise_for_status()
        src.write_bytes(r.content)
    im = ImageOps.exif_transpose(Image.open(src)).convert("RGB")
    h = round(W * im.height / im.width)
    im = im.resize((W, h), Image.LANCZOS)
    max_h = H - BOTTOM - TOP_MIN
    if h > max_h:                                   # rendu plus haut que 16:9 : on rogne un peu haut/bas, jamais les côtés
        cut = (h - max_h) // 2
        im = im.crop((0, cut, W, cut + max_h))
        h = max_h
    top = H - BOTTOM - h

    canvas = gradient(H)
    d = ImageDraw.Draw(canvas)
    # titre
    centered(d, (W // 2, top // 2), p["name"].upper(), font(74), WHITE)
    canvas.paste(im, (0, top))
    d = ImageDraw.Draw(canvas)
    y0 = top + h
    # stats : chambres | douches | m²
    stats = [(str(p["bedrooms"]), "chambres"), (str(p["bathrooms"]), "douches"), (str(p["surface"]), "m²")]
    col = W // 3
    for i, (num, lab) in enumerate(stats):
        cx = col * i + col // 2
        centered(d, (cx, y0 + 62), num, font(92), GOLD)
        centered(d, (cx, y0 + 132), lab, font(34), WHITE)
        if i:
            d.line([(col * i, y0 + 26), (col * i, y0 + 150)], fill=SOFT, width=2)
    if not price:
        # Sans prix : le bouton « TÉLÉCHARGER PLAN ET DEVIS » prend la place du prix (plus grand, bien visible)
        centered(d, (W // 2, y0 + 215), SUBLINE_NO_PRICE, font(33), SOFT)
        bw, bh, by = 900, 124, y0 + 262
        d.rounded_rectangle([(W - bw) // 2, by, (W + bw) // 2, by + bh], radius=62, fill=ORANGE)
        centered(d, (W // 2, by + bh // 2 - 2), CTA_NO_PRICE, font(47), TEAL_D)
        centered(d, (W // 2, by + bh + 42), "wooplans.com", font(32), SOFT)
    else:
        # prix
        centered(d, (W // 2, y0 + 205), "Plan + devis du modèle", font(32), SOFT)
        price_txt = f"{price:,}".replace(",", " ")
        fp, fc = font(104), font(46)
        wp = d.textlength(price_txt, font=fp)
        wc = d.textlength(" FCFA", font=fc)
        x = (W - (wp + wc)) / 2
        d.text((x, y0 + 270), price_txt, font=fp, fill=WHITE, anchor="lm")
        d.text((x + wp, y0 + 286), " FCFA", font=fc, fill=WHITE, anchor="lm")
        # CTA
        bw, bh, by = 800, 100, y0 + 340
        d.rounded_rectangle([(W - bw) // 2, by, (W + bw) // 2, by + bh], radius=50, fill=ORANGE)
        centered(d, (W // 2, by + bh // 2 - 2), "TÉLÉCHARGER MAINTENANT", font(42), TEAL_D)
        # adresse
        centered(d, (W // 2, by + bh + 38), "wooplans.com", font(32), SOFT)

    out = root / f"{p['code']}_4x5{suffix}.jpg"
    canvas.save(out, "JPEG", quality=92, optimize=True)
    return out


def sheet(paths, out_path, cols: int = 4, cell_w: int = 360) -> None:
    """Planche d'aperçu : chaque visuel en entier (4:5), pour validation par Tao."""
    cell_h = round(cell_w * H / W)
    rows = (len(paths) + cols - 1) // cols
    img = Image.new("RGB", (cols * cell_w, rows * cell_h), "white")
    for i, f in enumerate(paths):
        im = Image.open(f).convert("RGB").resize((cell_w - 6, cell_h - 6), Image.LANCZOS)
        img.paste(im, ((i % cols) * cell_w + 3, (i // cols) * cell_h + 3))
    img.save(out_path, "JPEG", quality=85, optimize=True)


def main(root: Path, price: int = None, no_price: bool = False) -> None:
    spec = json.loads((root / "spec.json").read_text(encoding="utf-8"))
    suffix = ""
    if no_price:
        spec["price_fcfa"], suffix = 0, "_sansprix"
    elif price and price != spec["price_fcfa"]:
        spec["price_fcfa"], suffix = price, f"_{price}"
    outs = []
    for p in spec["plans"]:
        outs.append(make(p, root, spec["price_fcfa"], suffix))
        print("OK", outs[-1])
    sheet(outs, root / f"apercu{suffix}.jpg")
    print("OK", root / f"apercu{suffix}.jpg")


if __name__ == "__main__":
    args = sys.argv[1:]
    price = None
    no_price = "--no-price" in args
    if no_price:
        args.remove("--no-price")
    if "--price" in args:
        i = args.index("--price")
        price = int(args[i + 1])
        del args[i:i + 2]
    main(Path(args[0]), price, no_price)
