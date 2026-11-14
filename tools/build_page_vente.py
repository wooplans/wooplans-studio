"""Page de vente du guide « Quelle maison construire avec votre budget ? » : un seul fichier HTML (images intégrées), pensé mobile d'abord.

Usage : python tools/build_page_vente.py [--url URL_CHARIOW] [--out guide/page_vente/index.html]
  --url : lien du produit Chariow (bouton « Obtenir le guide »). Sans --url, les boutons pointent vers « # ».
Aperçus : pages du PDF guide/guide_budget.pdf (pdftoppm). Textes : check_copy (montants autorisés : 1 900 FCFA).
"""
import argparse
import base64
import html
import io
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from wooplans import guardrails  # noqa: E402

PRICE = "1 900 FCFA"
WHATSAPP = "+237 6 94 32 77 85"
WA_LINK = "https://wa.me/237694327785"
PREVIEWS = [(1, "Couverture"), (4, "Sommaire par budget"), (6, "Fiche d'un modèle"), (15, "Fiche d'un duplex")]
FAQ = [
    ("Puis-je construire directement avec ce guide ?", "Non. Il sert à choisir un modèle et à situer votre budget. Pour construire, il faut les plans et un devis détaillé."),
    ("Les montants sont-ils fermes ?", "Non. Ce sont des estimations du devis de chaque modèle. Le coût réel dépend de votre ville, du terrain, des finitions et du moment de la construction."),
    ("Comment je reçois le guide ?", "Vous le téléchargez après le paiement."),
    ("Mon terrain est plus petit que celui indiqué. Que faire ?", "Chaque modèle indique le terrain prévu. Choisissez un modèle adapté à la surface dont vous disposez."),
]
RECOIT = [
    "20 modèles de villas et de duplex, en images, de 3 à 5 chambres",
    "4 tranches de budget : moins de 20 millions, de 20 à 40, de 40 à 60, plus de 60 millions de FCFA",
    "Pour chaque modèle : façade, chambres, niveaux, surface, terrain prévu et estimation du devis",
    "Une présentation du Catalogue Premium WooPlans à la fin, pour aller plus loin",
]


def b64(im: Image.Image, w: int) -> str:
    im = im.convert("RGB")
    im.thumbnail((w, w * 2))
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=82, optimize=True)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


def previews(pdf: Path) -> list:
    out = []
    with tempfile.TemporaryDirectory() as d:
        for n, label in PREVIEWS:
            subprocess.run(["pdftoppm", "-r", "110", "-f", str(n), "-l", str(n), "-png", "-singlefile", str(pdf), f"{d}/p{n}"], check=True)
            out.append((label, b64(Image.open(f"{d}/p{n}.png"), 520)))
    return out


def build(url: str) -> str:
    e = html.escape
    prev = previews(ROOT / "guide" / "guide_budget.pdf")
    FONT64 = base64.b64encode((ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf").read_bytes()).decode()
    cover = prev[0][1]
    texts = ["Quelle maison construire avec votre budget ?", "20 modèles classés par coût de construction. Le guide en images pour les personnes qui ont un terrain.",
             *RECOIT, *[x for q in FAQ for x in q], f"Prix : {PRICE}"]
    bad = [(t, guardrails.check_copy(t, {1900})) for t in texts if guardrails.check_copy(t, {1900})]
    if bad:
        raise SystemExit(f"check_copy : {bad}")
    cta = lambda label: f'<a class="btn" href="{e(url)}">{e(label)}</a>'
    gal = "".join(f'<figure><img src="{src}" alt="{e(label)}" loading="lazy"><figcaption>{e(label)}</figcaption></figure>' for label, src in prev[1:])
    faq = "".join(f"<details><summary>{e(q)}</summary><p>{e(a)}</p></details>" for q, a in FAQ)
    rec = "".join(f"<li>{e(x)}</li>" for x in RECOIT)
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Quelle maison construire avec votre budget ? · Guide WooPlans</title>
<meta name="description" content="20 modèles de villas et de duplex classés par coût de construction. Le guide en images : {PRICE}.">
<style>
@font-face{{font-family:'Poppins';font-weight:700;src:url(data:font/ttf;base64,{FONT64}) format('truetype')}}
:root{{--g:#0F5B59;--o:#F08A2E;--bg:#FAF8F4;--ink:#1d2b2b;--mut:#5c6b6b}}
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55;-webkit-text-size-adjust:100%}}
h1,h2{{font-family:Poppins,Inter,system-ui,sans-serif;font-weight:700;line-height:1.15}}
.w{{max-width:560px;margin:0 auto;padding:0 20px}}
.hero{{background:var(--g);color:#fff;padding:28px 0 36px;text-align:center}}
.hero .tag{{display:inline-block;background:var(--o);font-weight:700;font-size:12px;letter-spacing:2px;padding:5px 12px;border-radius:4px}}
.hero h1{{font-size:30px;margin:16px 0 12px}}.hero p.s{{color:#d6e8e7;font-size:17px}}
.hero img{{width:230px;border-radius:6px;box-shadow:0 10px 30px rgba(0,0,0,.4);margin:26px auto 8px;display:block}}
.price{{margin:18px 0 14px;font-size:15px;color:#d6e8e7}}.price b{{display:block;font-family:Poppins,Inter,system-ui,sans-serif;font-size:34px;color:#fff}}
.btn{{display:block;background:var(--o);color:#fff;text-decoration:none;text-align:center;font-family:Poppins,Inter,system-ui,sans-serif;font-weight:700;font-size:18px;padding:16px;border-radius:10px;box-shadow:0 4px 14px rgba(240,138,46,.45)}}
section{{padding:34px 0}}h2{{font-size:24px;color:var(--g);margin-bottom:14px}}
ul.ok{{list-style:none}}ul.ok li{{padding:11px 0 11px 34px;position:relative;border-bottom:1px solid #e8e4da}}ul.ok li:before{{content:'✓';position:absolute;left:0;top:10px;width:24px;height:24px;border-radius:50%;background:var(--o);color:#fff;font-weight:700;text-align:center;line-height:24px;font-size:14px}}
.gal{{display:grid;grid-template-columns:1fr 1fr;gap:12px}}.gal figure{{background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,.1)}}.gal img{{width:100%;display:block}}.gal figcaption{{font-size:13px;font-weight:600;color:var(--g);padding:8px 10px}}
.who{{background:#fff;border-left:5px solid var(--o);border-radius:6px;padding:16px 18px}}
.next{{background:var(--g);color:#fff;border-radius:12px;padding:22px}}.next h2{{color:#fff;font-size:21px}}.next p{{color:#d6e8e7}}
details{{background:#fff;border-radius:8px;padding:14px 16px;margin-bottom:10px;box-shadow:0 1px 5px rgba(0,0,0,.08)}}summary{{font-weight:600;cursor:pointer}}details p{{margin-top:8px;color:var(--mut)}}
.final{{text-align:center;background:#fff;padding:34px 0}}.final .price{{color:var(--mut)}}.final .price b{{color:var(--g)}}
footer{{text-align:center;color:var(--mut);font-size:14px;padding:22px 0 40px}}footer a{{color:var(--g)}}
.sticky{{position:sticky;bottom:0;background:rgba(250,248,244,.96);padding:10px 20px;border-top:1px solid #e6e1d4;z-index:5}}.sticky .btn{{max-width:520px;margin:0 auto;font-size:16px;padding:13px}}
</style></head><body>
<header class="hero"><div class="w"><span class="tag">GUIDE EN IMAGES</span>
<h1>Quelle maison construire avec votre budget ?</h1>
<p class="s">20 modèles classés par coût de construction. Le guide en images pour les personnes qui ont un terrain.</p>
<img src="{cover}" alt="Couverture du guide">
<div class="price">Prix<b>{PRICE}</b></div>{cta("Obtenir le guide")}</div></header>
<main class="w">
<section><div class="who"><b>Pour qui ?</b><br>Vous avez un terrain, ou vous allez en acheter un, et vous voulez savoir quelle maison correspond à votre budget avant de parler à un maçon ou à un architecte.</div></section>
<section><h2>Ce que vous recevez</h2><ul class="ok">{rec}</ul></section>
<section><h2>Un aperçu du guide</h2><div class="gal">{gal}</div></section>
<section><div class="next"><h2>Pour aller plus loin</h2><p>La dernière page du guide présente le Catalogue Premium WooPlans : 100 modèles de plans, avec pour chacun le plan de distribution et le devis, de la fondation jusqu'aux finitions.</p></div></section>
<section><h2>Questions fréquentes</h2>{faq}</section>
</main>
<div class="final"><div class="w"><h2>Choisissez votre maison avant de construire</h2><div class="price">Prix<b>{PRICE}</b></div>{cta("Obtenir le guide")}</div></div>
<footer><div class="w">Une question ? Écrivez-nous sur WhatsApp : <a href="{WA_LINK}">{WHATSAPP}</a><br>wooplans.com</div></footer>
<div class="sticky">{cta("Obtenir le guide · " + PRICE)}</div>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--url", default="#")
    ap.add_argument("--out", default=str(ROOT / "guide" / "page_vente" / "index.html"))
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(a.url), encoding="utf-8")
    print("Page de vente :", out, f"{out.stat().st_size / 1e3:.0f} Ko")


if __name__ == "__main__":
    main()
