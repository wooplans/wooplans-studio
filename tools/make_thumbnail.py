"""Vignette (couverture 9:16) d'une vidéo de visite : OBLIGATOIRE avant toute publication (elle attire l'attention).

  python tools/make_thumbnail.py visite_plan/jobs/<id> [sortie.jpg]

Fond : facade.png du job (visite avec 3D) sinon plan.png sur fond clair. Textes : bloc "thumbnail" de PUBLISH.json
  {"title": "Combien coûte cette maison ?", "badge": "31 170 020 FCFA", "chip": "4 chambres · plain-pied"}
À défaut, déduits de bump.json (tag, chip, target = total « clé en main » du devis) ou de meta.json (band).
Aucun montant hors devis : le badge passe par wooplans.guardrails.check_copy (montant autorisé = celui du job).
"""
import json
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
FONT = ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf"
GREEN, ORANGE, W, H = (15, 91, 89), (240, 138, 46), 1080, 1920


def fit_font(draw, text, size, max_w):
    while size > 28:
        f = ImageFont.truetype(str(FONT), size)
        if draw.textlength(text, font=f) <= max_w:
            return f
        size -= 4
    return ImageFont.truetype(str(FONT), 28)


def wrap(draw, text, size, max_w):
    words, lines, cur = text.split(), [], ""
    for w in words:
        t = (cur + " " + w).strip()
        if draw.textlength(t, font=ImageFont.truetype(str(FONT), size)) <= max_w or not cur:
            cur = t
        else:
            lines.append(cur); cur = w
    return lines + [cur]


def load_job(job: Path):
    cfg = {}
    if (job / "PUBLISH.json").exists():
        cfg = json.loads((job / "PUBLISH.json").read_text(encoding="utf-8")).get("thumbnail", {})
    bump = json.loads((job / "bump.json").read_text(encoding="utf-8")) if (job / "bump.json").exists() else {}
    meta = json.loads((job / "meta.json").read_text(encoding="utf-8")) if (job / "meta.json").exists() else {}
    title = cfg.get("title") or ("Combien coûte cette maison ?" if bump.get("target") else "Visite guidée du plan")
    badge = cfg.get("badge") or (f"{bump['target']:,}".replace(",", " ") + " FCFA" if bump.get("target") else "")
    chip = cfg.get("chip") or bump.get("chip", "").replace("·", "·").capitalize() or meta.get("band", "")
    return title, badge, chip, bump.get("target")


def main() -> int:
    job = Path(sys.argv[1])
    out = Path(sys.argv[2]) if len(sys.argv) > 2 else job / "thumb.jpg"
    title, badge, chip, target = load_job(job)
    from wooplans.guardrails import check_copy
    problems = check_copy(" ".join([title, badge, chip]), allowed_amounts=[target] if target else [])
    if problems:
        print("Texte de vignette refusé :", problems)
        return 1
    img = Image.new("RGB", (W, H), (255, 255, 255))
    src = job / "facade.png"
    if src.exists():
        bg = Image.open(src).convert("RGB")
        k = H / bg.height
        bg = bg.resize((round(bg.width * k), H), Image.LANCZOS)
        img.paste(bg, ((W - bg.width) // 2, 0))
    else:
        bg = Image.open(job / "plan.png").convert("RGB")
        k = min(W * 0.96 / bg.width, 1050 / bg.height)
        bg = bg.resize((round(bg.width * k), round(bg.height * k)), Image.LANCZOS)
        img.paste(bg, ((W - bg.width) // 2, 520))
    # dégradés pour la lisibilité
    ov = Image.new("RGBA", (W, H), (0, 0, 0, 0)); od = ImageDraw.Draw(ov)
    for y in range(760):
        od.line([(0, y), (W, y)], fill=(8, 40, 40, int(215 * (1 - y / 760))))
    for y in range(H - 640, H):
        od.line([(0, y), (W, y)], fill=(8, 40, 40, int(225 * ((y - (H - 640)) / 640))))
    img = Image.alpha_composite(img.convert("RGBA"), ov).convert("RGB")
    d = ImageDraw.Draw(img)
    y = 150                                                  # titre (zone sûre : > 130 px du haut)
    for line in wrap(d, title.upper(), 92, W - 140):
        f = fit_font(d, line, 92, W - 140)
        d.text((W // 2, y), line, font=f, fill="white", anchor="ma", stroke_width=7, stroke_fill=GREEN)
        y += 112
    if badge:                                                # prix du devis (clé en main)
        f = fit_font(d, badge, 96, W - 200)
        tw = d.textlength(badge, font=f); bx0, by0 = (W - tw) / 2 - 44, y + 24
        d.rounded_rectangle([bx0, by0, bx0 + tw + 88, by0 + 150], radius=75, fill=ORANGE, outline="white", width=6)
        d.text((W / 2, by0 + 76), badge, font=f, fill="white", anchor="mm")
        y = by0 + 150
    if chip:                                                 # sous le centre, au-dessus de la bande du bas
        f = fit_font(d, chip.upper(), 52, W - 160)
        d.text((W // 2, 1610), chip.upper(), font=f, fill=(231, 195, 108), anchor="ma", stroke_width=4, stroke_fill=GREEN)
    d.rectangle([0, 1730, W, H], fill=GREEN)                 # bande wooplans.com
    d.rectangle([0, 1730, W, 1738], fill=ORANGE)
    logo = ROOT / "assets" / "brand" / "logo_white.png"
    f = ImageFont.truetype(str(FONT), 76)
    if logo.exists():
        lg = Image.open(logo).convert("RGBA"); lg = lg.resize((round(lg.width * 112 / lg.height), 112), Image.LANCZOS)
        tw = d.textlength("wooplans.com", font=f); x0 = (W - (lg.width + 34 + tw)) / 2
        img.paste(lg, (round(x0), 1790), lg)
        d.text((x0 + lg.width + 34, 1846), "wooplans.com", font=f, fill="white", anchor="lm")
    else:
        d.text((W / 2, 1846), "wooplans.com", font=f, fill="white", anchor="mm")
    out.parent.mkdir(parents=True, exist_ok=True)
    img.save(out, "JPEG", quality=88, optimize=True)
    print("vignette :", out, f"{out.stat().st_size // 1024} Ko")
    return 0


if __name__ == "__main__":
    sys.exit(main())
