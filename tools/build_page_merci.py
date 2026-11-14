"""Page de remerciement du guide (après paiement) avec l'offre du Catalogue Premium : un seul fichier HTML, mobile d'abord.

Usage : python tools/build_page_merci.py --img DOSSIER_IMG [--download-url URL] [--out guide/page_merci/index.html]
  --img          : dossier out/img de tools/build_guide.py (plan_rdc.jpg, plan_etage.jpg : plans du D4-006 floutés)
  --download-url : lien de téléchargement du guide (Chariow). Sans lui, le bouton pointe vers « # ».
Le bouton de l'offre pointe vers la page catalogue avec l'UTM `build_guide_link("merci")`.
Textes : check_copy (montants autorisés : 39 000 FCFA, prix actuel du catalogue).
"""
import argparse
import base64
import html
import io
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.build_guide import COUVERTURE, LOTS_EXEMPLE  # noqa: E402
from wooplans import guardrails  # noqa: E402
from wooplans.utm import build_guide_link  # noqa: E402

WHATSAPP = "+237 6 94 32 77 85"
WA_LINK = "https://wa.me/237694327785"


def b64(path: Path, w: int, fmt="JPEG") -> str:
    im = Image.open(path).convert("RGB")
    im.thumbnail((w, w * 2))
    buf = io.BytesIO()
    im.save(buf, fmt, quality=84)
    return f"data:image/{fmt.lower()};base64," + base64.b64encode(buf.getvalue()).decode()


def build(img: Path, download_url: str) -> str:
    e = html.escape
    link = build_guide_link("merci")
    book = b64(COUVERTURE, 620)
    rdc, etage = b64(img / "plan_rdc.jpg", 420), b64(img / "plan_etage.jpg", 420)
    font = base64.b64encode((ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf").read_bytes()).decode()
    steps = ["Repérez votre tranche de budget.", "Notez 2 ou 3 modèles qui vous plaisent.", "Vérifiez que votre terrain a la surface prévue."]
    lots = "".join(f'<div class="lot"><i>{n}</i><span>{e(l)}</span>' + (f'<b>{a:,} FCFA</b>'.replace(",", " ") if a else '<em></em>') + "</div>" for n, (l, a) in enumerate(LOTS_EXEMPLE, 1))
    texts = ["Merci. Votre guide est prêt.", *steps, "Vous avez fait le premier pas.",
             "Nous avons réuni 100 modèles de plans dans un catalogue. Pour chacun, vous pouvez consulter le plan de distribution et le devis, de la fondation jusqu'aux finitions.",
             "Prix actuel : 39 000 FCFA"]
    bad = [(t, guardrails.check_copy(t, set())) for t in texts if guardrails.check_copy(t, set())]
    if bad:
        raise SystemExit(f"check_copy : {bad}")
    st = "".join(f"<li><b>{i}</b><span>{e(s)}</span></li>" for i, s in enumerate(steps, 1))
    return f"""<!doctype html><html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Merci · Votre guide WooPlans est prêt</title>
<style>
@font-face{{font-family:'Poppins';font-weight:700;src:url(data:font/ttf;base64,{font}) format('truetype')}}
:root{{--g:#0F5B59;--o:#F08A2E;--bg:#FAF8F4;--ink:#1d2b2b;--mut:#5c6b6b}}
*{{box-sizing:border-box;margin:0;padding:0}}body{{font-family:Inter,system-ui,sans-serif;background:var(--bg);color:var(--ink);line-height:1.55;-webkit-text-size-adjust:100%}}
h1,h2,h3,.pop{{font-family:Poppins,Inter,system-ui,sans-serif;font-weight:700;line-height:1.15}}
.w{{max-width:560px;margin:0 auto;padding:0 20px}}
.top{{background:var(--g);color:#fff;text-align:center;padding:30px 0 34px}}
.ok{{width:58px;height:58px;border-radius:50%;background:var(--o);margin:0 auto 14px;font-size:32px;line-height:58px;font-weight:700}}
.top h1{{font-size:28px;margin-bottom:10px}}.top p{{color:#d6e8e7;margin-bottom:20px}}
.btn{{display:block;background:var(--o);color:#fff;text-decoration:none;text-align:center;font-family:Poppins,Inter,system-ui,sans-serif;font-weight:700;font-size:17px;padding:15px;border-radius:10px;box-shadow:0 4px 14px rgba(240,138,46,.4)}}
.btn.w2{{background:#fff;color:var(--g);box-shadow:none}}
section{{padding:30px 0}}h2{{font-size:22px;color:var(--g);margin-bottom:12px}}
ol.s{{list-style:none}}ol.s li{{display:flex;gap:14px;align-items:center;padding:10px 0;border-bottom:1px solid #e8e4da}}ol.s b{{background:var(--o);color:#fff;border-radius:50%;width:28px;height:28px;flex:none;text-align:center;line-height:28px;font-family:Poppins}}
.up{{background:var(--g);color:#fff;padding:34px 0 40px}}
.up .tag{{display:inline-block;background:var(--o);font-weight:700;font-size:12px;letter-spacing:2px;padding:5px 12px;border-radius:4px}}
.up h2{{color:#fff;font-size:25px;margin:14px 0 10px}}.up p{{color:#d6e8e7}}
.book{{display:block;width:250px;margin:26px auto 8px;border-radius:6px;box-shadow:0 14px 34px rgba(0,0,0,.5)}}
.ex{{margin-top:22px;font-family:Poppins,Inter,system-ui,sans-serif;font-weight:700;font-size:12px;letter-spacing:1.5px;color:#ffc38a;text-transform:uppercase}}
.pl{{display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-top:10px}}.pl figure{{background:#fff;border-radius:8px;padding:6px;text-align:center}}.pl img{{width:100%;height:150px;object-fit:contain;display:block}}.pl figcaption{{color:var(--g);font-size:12px;font-weight:600;margin-top:2px}}
.dv{{background:#fff;color:var(--ink);border-radius:8px;padding:12px 14px;margin-top:10px}}.dv h3{{font-size:14px;color:var(--g);margin-bottom:6px}}
.lot{{display:flex;align-items:center;gap:8px;font-size:13px;padding:4px 0;border-bottom:1px solid #eef1f1}}.lot i{{font-style:normal;color:var(--o);font-family:Poppins;width:18px}}.lot span{{flex:1}}.lot b{{color:var(--g)}}.lot em{{width:70px;height:9px;background:linear-gradient(90deg,#c9d3d3,#e6ecec);border-radius:4px}}
.note{{font-size:12px;color:#8a4a0f;text-align:center;margin-top:8px}}
.price{{display:inline-block;background:#fff;color:var(--g);border-radius:10px;padding:10px 20px;font-family:Poppins,Inter,system-ui,sans-serif;font-weight:700;font-size:20px;margin:24px 0 14px}}
.skip{{text-align:center;color:#a9c9c7;font-size:14px;margin-top:16px}}
footer{{text-align:center;color:var(--mut);font-size:14px;padding:24px 0 40px}}footer a{{color:var(--g)}}
</style></head><body>
<header class="top"><div class="w"><div class="ok">✓</div><h1>Merci. Votre guide est prêt.</h1><p>Téléchargez-le avec le bouton ci-dessous.</p>
<a class="btn" href="{e(download_url)}">Télécharger le guide</a></div></header>
<main class="w"><section><h2>Pour bien l'utiliser</h2><ol class="s">{st}</ol></section></main>
<div class="up"><div class="w"><span class="tag">VOUS AVEZ FAIT LE PREMIER PAS</span>
<h2>Nous avons réuni 100 modèles de plans dans un catalogue.</h2>
<p>Pour chacun, vous pouvez consulter <b style="color:#fff">le plan de distribution</b> et <b style="color:#fff">le devis, de la fondation jusqu'aux finitions</b>.</p>
<img class="book" src="{book}" alt="Catalogue Premium WooPlans : 100 modèles, villas et duplex">
<div class="ex">Exemple : Duplex D4-006</div>
<div class="pl"><figure><img src="{rdc}" alt="Plan RDC"><figcaption>Plan de distribution · RDC</figcaption></figure><figure><img src="{etage}" alt="Plan étage"><figcaption>Plan de distribution · étage</figcaption></figure></div>
<div class="dv"><h3>Devis par lots, de la fondation aux finitions</h3>{lots}<div class="note">🔒 Plans lisibles et montants complets dans le Catalogue Premium</div></div>
<div style="text-align:center"><div class="price">Prix actuel : 39 000 FCFA</div></div>
<a class="btn" href="{e(link)}">Découvrir le Catalogue Premium</a>
<p class="skip">Vous pouvez aussi le faire plus tard : wooplans.com/catalogue-premium</p></div></div>
<footer><div class="w">Une question sur un modèle ? Écrivez-nous sur WhatsApp : <a href="{WA_LINK}">{WHATSAPP}</a><br>wooplans.com</div></footer>
</body></html>"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--download-url", default="#")
    ap.add_argument("--out", default=str(ROOT / "guide" / "page_merci" / "index.html"))
    a = ap.parse_args()
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(Path(a.img), a.download_url), encoding="utf-8")
    print("Page de remerciement :", out, f"{out.stat().st_size / 1e3:.0f} Ko")


if __name__ == "__main__":
    main()
