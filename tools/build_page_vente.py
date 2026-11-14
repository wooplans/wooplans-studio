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
    ap.add_argument("--site", help="racine du dépôt du site (wooplans/wooplans) : écrit public/lp/guide-budget.html, paiement par l'API du site")
    a = ap.parse_args()
    if a.site:
        out = Path(a.site) / "public" / "lp" / "guide-budget.html"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(build_site(Path(a.site)), encoding="utf-8")
        print("Page de vente (site) :", out, f"{out.stat().st_size / 1e3:.0f} Ko")
        return
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(build(a.url), encoding="utf-8")
    print("Page de vente :", out, f"{out.stat().st_size / 1e3:.0f} Ko")



# ───────────── Version hébergée sur le site (wooplans/wooplans) : paiement par l'API Chariow du site ─────────────
SITE_WA = "https://wa.me/237694327885?text=Bonjour%20WOOPLANS%2C%20j%27ai%20une%20question%20sur%20le%20guide."
MODAL_CSS = """
button.btn{width:100%;border:0;cursor:pointer;font-size:inherit}
.ov{position:fixed;inset:0;background:rgba(0,0,0,.55);display:none;align-items:flex-end;justify-content:center;z-index:50}.ov.on{display:flex}
.sheet{position:relative;background:#fff;width:100%;max-width:480px;border-radius:18px 18px 0 0;padding:22px 20px 20px;max-height:94vh;overflow:auto}
.sheet .close{position:absolute;top:10px;right:12px;border:0;background:none;font-size:22px;cursor:pointer;color:#5c6b6b}
.sheet .eyebrow{font-size:12px;letter-spacing:2px;text-transform:uppercase;color:var(--o);font-weight:700}.sheet h3{font-family:Poppins,Inter,system-ui,sans-serif;font-size:21px;color:var(--g);margin:4px 0 12px}
.ckform label{display:block;font-size:13px;font-weight:600;margin:12px 0 4px}.ckform input{width:100%;padding:12px;border:1px solid #cfd6d6;border-radius:8px;font-size:16px}
.ckform .row{display:flex;gap:8px}.dial{position:relative;display:flex;align-items:center;gap:4px;border:1px solid #cfd6d6;border-radius:8px;padding:0 10px;min-width:92px;font-size:16px}.dial select{position:absolute;inset:0;opacity:0;width:100%;font-size:16px}
.ckprice{display:flex;justify-content:space-between;align-items:center;background:#f3f7f7;border-radius:10px;padding:10px 14px}.ckprice p{font-size:13px;color:#5c6b6b;max-width:60%}.ckprice b{font-family:Poppins,Inter,system-ui,sans-serif;font-size:22px;color:var(--g)}
.ckform .cta{width:100%;margin-top:16px;border:0;border-radius:10px;background:var(--o);color:#fff;font-family:Poppins,Inter,system-ui,sans-serif;font-weight:700;font-size:17px;padding:15px;cursor:pointer}.ckform .cta:disabled{opacity:.6}
.err{color:#b42318;font-size:14px;margin-top:10px}.secure,.wahelp{font-size:13px;color:#5c6b6b;text-align:center;margin-top:10px}.wahelp a{color:var(--g)}
"""
MODAL_HTML = """
<div class="ov" id="checkout" onclick="if(event.target===this)closeCheckout()" aria-hidden="true">
  <div class="sheet" role="dialog" aria-modal="true" aria-labelledby="ckTitle">
    <button class="close" onclick="closeCheckout()" aria-label="Fermer">✕</button>
    <p class="eyebrow">Guide en images</p>
    <h3 id="ckTitle">Obtenez votre guide</h3>
    <form class="ckform ph-no-capture" id="ckForm" onsubmit="return pay(event)" novalidate>
      <div class="ckprice"><p>Le guide en PDF, à télécharger après le paiement.</p><b>1&nbsp;900&nbsp;FCFA</b></div>
      <div><label for="ckName">Nom complet</label><input id="ckName" name="name" required minlength="2" autocomplete="name" placeholder="Jean Dupont"></div>
      <div><label for="ckEmail">Email</label><input id="ckEmail" name="email" type="email" required autocomplete="email" inputmode="email" placeholder="vous@exemple.com"></div>
      <div><label for="ckPhone">Numéro Mobile Money / WhatsApp</label>
        <div class="row"><div class="dial"><span id="ckDial">+225</span><small aria-hidden="true">▾</small>__SELECT__</div>
        <input id="ckPhone" name="phone" type="tel" required inputmode="tel" autocomplete="tel-national" placeholder="07 01 23 45 67"></div></div>
      <p class="err" id="ckErr" hidden></p>
      <button class="cta" type="submit" id="ckBtn">Payer 1&nbsp;900&nbsp;FCFA</button>
      <p class="secure">🔒 Paiement sécurisé par Mobile Money ou carte bancaire</p>
    </form>
    <p class="wahelp">Un souci pour payer ? <a href="__WA__" data-wa="payment_help" target="_blank" rel="noopener">Écrivez-nous sur WhatsApp</a></p>
  </div>
</div>
"""
SITE_JS = """<script>
function wpTrack(type,ctaId){try{var body=JSON.stringify({type:type,ctaId:ctaId||undefined,url:location.href,referrer:document.referrer||null});
 if(navigator.sendBeacon)navigator.sendBeacon('/api/t',new Blob([body],{type:'application/json'}));else fetch('/api/t',{method:'POST',headers:{'Content-Type':'application/json'},body:body,keepalive:true});}catch(e){}}
window.wpVid=fetch('/api/t',{method:'POST',headers:{'Content-Type':'application/json'},keepalive:true,body:JSON.stringify({type:'sales_page_view',ctaId:'guide_budget',url:location.href,referrer:document.referrer||null})})
 .then(function(r){return r.json()}).then(function(d){return d.vid||null}).catch(function(){return null});
try{fbq('track','ViewContent',{content_name:'Guide : Quelle maison construire avec votre budget ?',content_ids:['guide_budget'],content_type:'product',value:1900,currency:'XAF'});}catch(_){}
document.addEventListener('click',function(e){var wa=e.target.closest&&e.target.closest('a[href*="wa.me"]');if(wa){var id=(wa.getAttribute('data-wa')||'guide')+'@guide';wpTrack('whatsapp_click',id);wpCapture('whatsapp_click',{cta_id:id});}},true);
var ckCta='guide@hero',openedAt=0,countryChosen=false,countryAsked=false;
function setCountry(sel,auto){var o=sel.options[sel.selectedIndex];document.getElementById('ckDial').textContent='+'+o.getAttribute('data-dial');document.getElementById('ckPhone').placeholder=o.getAttribute('data-ex')||'';if(!auto)countryChosen=true;}
function guessCountry(){if(countryAsked)return;countryAsked=true;
 fetch('/api/pays',{cache:'no-store'}).then(function(r){return r.json()}).then(function(d){var sel=document.getElementById('ckForm').elements.namedItem('countryCode');if(countryChosen||!d||!d.country)return;
 for(var i=0;i<sel.options.length;i++)if(sel.options[i].value===d.country){sel.selectedIndex=i;setCountry(sel,true);return;}}).catch(function(){});}
function pay(e){e.preventDefault();
 var f=document.getElementById('ckForm'),err=document.getElementById('ckErr'),btn=document.getElementById('ckBtn');
 var el=function(n){return f.elements.namedItem(n)},cc=el('countryCode'),raw=el('phone').value;
 var d={name:el('name').value.trim(),email:el('email').value.trim(),countryCode:cc.value,phone:raw.replace(/\\D/g,'')};
 var dial=cc.options[cc.selectedIndex].getAttribute('data-dial');
 if(dial&&d.phone.indexOf(dial)===0&&/^\\s*\\+/.test(raw))d.phone=d.phone.slice(dial.length);else if(dial&&d.phone.indexOf('00'+dial)===0)d.phone=d.phone.slice(dial.length+2);
 if(d.name.length<2||!/^[^\\s@]+@[^\\s@]+\\.[^\\s@]+$/.test(d.email)||d.phone.length<6){err.textContent='Merci de renseigner votre nom, un email valide et votre numéro.';err.hidden=false;return false}
 err.hidden=true;btn.disabled=true;var label=btn.innerHTML;btn.textContent='Ouverture du paiement…';
 fetch('/api/guide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(d)})
  .then(function(r){return r.json().then(function(j){return{ok:r.ok,j:j}})})
  .then(function(r){if(!r.ok||!r.j.url)throw new Error(r.j&&r.j.error||'');
   wpCapture('checkout_redirect',{cta_id:ckCta,provider:'chariow'});
   var done=false,once=function(){if(!done){done=true;location.href=r.j.url}};
   try{fbq('track','InitiateCheckout',{content_name:'Guide : Quelle maison construire avec votre budget ?',content_ids:['guide_budget'],content_type:'product',value:1900,currency:'XAF'},r.j.metaEventId?{eventID:r.j.metaEventId}:{});}catch(_){}
   setTimeout(once,300);})
  .catch(function(x){err.textContent=x.message||"Le paiement n'a pas pu démarrer. Réessayez ou écrivez-nous sur WhatsApp.";err.hidden=false;btn.disabled=false;btn.innerHTML=label});
 return false;}
function buy(btn){ckCta=(btn&&btn.getAttribute('data-cta')||'hero');ckCta='guide@'+ckCta;wpTrack('cta_click',ckCta);wpCapture('cta_click',{cta_id:ckCta});wpCapture('checkout_open',{cta_id:ckCta,mode:'form',provider:'chariow'});
 var ov=document.getElementById('checkout');ov.classList.add('on');ov.setAttribute('aria-hidden','false');document.body.style.overflow='hidden';openedAt=Date.now();guessCountry();}
function closeCheckout(){var ov=document.getElementById('checkout');if(ov.classList.contains('on'))wpCapture('checkout_close',{open_ms:Date.now()-openedAt,form_shown:true});ov.classList.remove('on');ov.setAttribute('aria-hidden','true');document.body.style.overflow='';}
document.addEventListener('keydown',function(e){if(e.key==='Escape')closeCheckout()});
</script>"""


def build_site(site_root: Path) -> str:
    import re
    cat = (site_root / "public" / "lp" / "catalogue-premium.html").read_text(encoding="utf-8")
    start = cat.index("<!-- Mesure : Pixel Meta")
    end = cat.index("</script>", cat.index("<script>", start)) + len("</script>")
    measure = cat[start:end]                                     # mesure du site : Pixel Meta, PostHog, consentement en Europe
    select = re.search(r'<select name="countryCode".*?</select>', cat, re.S).group(0).replace('<option value="CI"', '<option value="CI" selected')
    page = build("#")
    sticky = iter(["hero", "final", "sticky"])
    page = re.sub(r'<a class="btn" href="#">(.*?)</a>', lambda m: f'<button type="button" class="btn" data-cta="{next(sticky)}" onclick="buy(this)">{m.group(1)}</button>', page)
    page = page.replace(f'<a href="{WA_LINK}">{WHATSAPP}</a>', f'<a href="{SITE_WA}" data-wa="footer" target="_blank" rel="noopener">WhatsApp</a>')
    assert 'onclick="buy(this)"' in page and "data-wa=" in page
    head = "<meta name=\"robots\" content=\"noindex,nofollow\"><script>var WP_VARIANT='guide';</script>" + measure
    page = page.replace("</head>", head + "</head>", 1).replace("</style>", MODAL_CSS + "</style>", 1)
    return page.replace("</body>", MODAL_HTML.replace("__SELECT__", select).replace("__WA__", SITE_WA) + SITE_JS + "</body>")

if __name__ == "__main__":
    main()
