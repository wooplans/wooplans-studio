"""Traitement d'images pour les posts : JPEG propre avec filigrane discret, planche d'aperçu pour validation."""
import io
from typing import List, Tuple

from PIL import Image, ImageDraw, ImageFont, ImageOps

from wooplans.settings import ROOT

WM = ROOT / "assets" / "brand" / "wm_logo.png"
FONT = ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf"


def prepare_image(data: bytes, watermark: bool = True, max_side: int = 1600) -> bytes:
    """Rendu du catalogue (webp, png…) → JPEG, côté long ≤ 1600 px, filigrane WooPlans discret en bas à droite."""
    im = ImageOps.exif_transpose(Image.open(io.BytesIO(data))).convert("RGB")
    s = min(1.0, max_side / max(im.size))
    if s < 1:
        im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    if watermark and WM.is_file():
        wm = Image.open(WM).convert("RGBA")
        tw = max(120, round(im.width * 0.24))
        wm = wm.resize((tw, round(wm.height * tw / wm.width)), Image.LANCZOS)
        wm.putalpha(wm.getchannel("A").point(lambda v: int(v * 0.6)))
        m = round(im.width * 0.03)
        im = im.convert("RGBA")
        im.alpha_composite(wm, (im.width - tw - m, im.height - wm.height - m))
        im = im.convert("RGB")
    out = io.BytesIO()
    im.save(out, "JPEG", quality=88, optimize=True)
    return out.getvalue()


def _font(size: int):
    try:
        return ImageFont.truetype(str(FONT), size)
    except Exception:
        return ImageFont.load_default()


def contact_sheet(items: List[Tuple[Image.Image, str, str]], out_path, cols: int = 3, cell: int = 360, bar: int = 86) -> None:
    """Planche d'aperçu : une case par post (miniature carrée + 2 lignes de texte)."""
    rows = (len(items) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * cell, rows * (cell + bar)), "white")
    d = ImageDraw.Draw(sheet)
    f1, f2 = _font(22), _font(19)
    for i, (im, l1, l2) in enumerate(items):
        x, y = (i % cols) * cell, (i // cols) * (cell + bar)
        thumb = ImageOps.fit(im.convert("RGB"), (cell - 6, cell - 6), Image.LANCZOS)
        sheet.paste(thumb, (x + 3, y + 3))
        d.text((x + 10, y + cell + 6), l1, fill="#0F5B59", font=f1)
        d.text((x + 10, y + cell + 40), l2, fill="#333333", font=f2)
    sheet.save(out_path, "JPEG", quality=82, optimize=True)
