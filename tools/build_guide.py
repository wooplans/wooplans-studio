"""Guide d'entrée « Quelle maison construire avec votre budget ? » : textes, HTML et PDF (Chromium).

Usage :
  python tools/build_guide.py --src DOSSIER_ORIGINAUX [--whatsapp "+237 ..."] [--out guide/out]
  python tools/build_guide.py --texts            # régénère guide/TEXTES.md seulement

Les originaux (un par modèle, nommés CODE.png / CODE.jpg, ex. V3-027.png) sont des rendus propres de R2 : ils ne sont
jamais copiés dans le dépôt. Chaque image reçoit le filigrane WooPlans et est réduite avant d'entrer dans le PDF.
Chiffres : uniquement data/plans.json (catalogue en ligne), arrondis au dixième de million. Textes : check_copy.
"""
import argparse
import html
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from wooplans import guardrails  # noqa: E402
from wooplans.image_tools import prepare_image  # noqa: E402
from wooplans.utm import build_guide_link  # noqa: E402

TITLE = "Quelle maison construire avec votre budget ?"
TRANCHES = [
    ("Moins de 20 millions FCFA", "Les premières maisons", "< 20 M", ["V3-027", "V3-002", "V3-003", "V3-025", "V3-038"]),
    ("De 20 à 40 millions FCFA", "Villas plus grandes et premiers duplex", "20–40 M", ["V3-009", "V4-010", "V5-008", "D4-036", "D4-034"]),
    ("De 40 à 60 millions FCFA", "Des duplex de 4 et 5 chambres", "40–60 M", ["D4-006", "D5-016", "D5-012", "D4-026", "D4-007"]),
    ("Plus de 60 millions FCFA", "Les grandes maisons", "60 M +", ["D4-017", "D4-003", "D5-019", "D5-018", "D4-001"]),
]
COVER_CODE = "D4-003"


def millions(n: int) -> str:
    s = f"{round(n / 1e6, 1):.1f}".replace(".", ",")
    return s[:-2] if s.endswith(",0") else s


def pages(plans: dict, whatsapp: str = None) -> list:
    """Liste de pages : dict(kind, nav, title, body, [code, chips, estimate])."""
    link = build_guide_link("page28")
    rng = lambda codes: (millions(min(plans[c]["estimate_total"] for c in codes)), millions(max(plans[c]["estimate_total"] for c in codes)))
    P = [
        dict(kind="cover", nav="1 · Couverture", title=TITLE, body="20 modèles classés par coût de construction\nwooplans.com"),
        dict(kind="text", nav="2 · Comment utiliser ce guide", title="Vous avez un terrain. Quelle maison pour votre budget ?",
             body="C'est toujours la première question. Ce guide y répond en images.\n\nLes 20 modèles sont classés en quatre tranches de budget, des plus accessibles aux plus ambitieux. Pour chacun : une façade, le nombre de chambres, la surface, le terrain prévu et l'estimation du devis.\n\nComment s'en servir :\n1. Repérez la tranche qui correspond à votre budget total.\n2. Regardez les modèles de cette tranche, puis ceux de la tranche voisine.\n3. Notez les 2 ou 3 qui vous plaisent.\n4. Vérifiez que votre terrain a la surface prévue."),
        dict(kind="text", nav="3 · Ce que veut dire « estimation »", title="Une estimation, pas un prix ferme",
             body="Chaque montant de ce guide est l'estimation du devis WooPlans du modèle, arrondie au dixième de million de FCFA.\n\nLe coût réel d'une construction dépend de votre ville, de l'accès au terrain, de la nature du sol, des finitions que vous choisissez et du moment où vous construisez.\n\nCes montants servent à comparer les modèles entre eux et à situer votre budget. Pour votre projet, demandez toujours un devis local à des professionnels."),
        dict(kind="toc", nav="4 · Sommaire", title="Choisissez votre tranche de budget",
             body="\n".join(f"{t} : {len(c)} modèles, de {rng(c)[0]} à {rng(c)[1]} millions FCFA" for t, _, _, c in TRANCHES)),
    ]
    for i, (t, sub, badge, codes) in enumerate(TRANCHES):
        lo, hi = rng(codes)
        P.append(dict(kind="divider", nav=f"Intercalaire {i + 1}", title=t, badge=badge,
                      body=f"{sub}.\n5 modèles, de {lo} à {hi} millions FCFA (estimation du devis)."))
        for c in codes:
            p = plans[c]
            villa = p["category"] == "villa"
            niv = "de plain-pied" if p["levels"] == 1 else f"sur {p['levels']} niveaux"
            ch = f"{p['bedrooms']} chambres"
            chips = [ch, "plain-pied" if p["levels"] == 1 else f"{p['levels']} niveaux", f"{p['surface']} m²", f"terrain prévu : {p['land_area']} m²"]
            est = f"environ {millions(p['estimate_total'])} millions FCFA"
            sent = (f"{'Une villa' if villa else 'Un duplex'} {niv} de {ch}, d'une surface de {p['surface']} m², "
                    f"{'prévue' if villa else 'prévu'} pour un terrain de {p['land_area']} m².")
            body = (f"{' · '.join(chips)}\nEstimation du devis : {est}\n\n{sent}\n\nRetrouvez ce modèle sur wooplans.com")
            P.append(dict(kind="model", nav=f"Modèle {c}", title=f"{'Villa' if villa else 'Duplex'} {c}", code=c, chips=chips,
                          estimate=est, sentence=sent, body=body))
    P += [
        dict(kind="text", nav="25 · Choisir selon votre terrain et votre famille", title="Quatre vérifications simples",
             body="Terrain : chaque modèle indique le terrain prévu. Votre terrain doit être au moins aussi grand, avec de la place pour les accès.\n\nFamille : comptez les chambres dont vous avez besoin aujourd'hui, et celles dont vous aurez besoin dans 5 à 10 ans.\n\nPlain-pied ou duplex : le plain-pied demande plus de surface au sol ; le duplex en demande moins, sur deux niveaux.\n\nBudget : gardez une marge au-dessus de l'estimation, pour les imprévus et les finitions."),
        dict(kind="text", nav="26 · Cinq questions avant de construire", title="Avant de poser la première pierre",
             body="1. Quel est mon budget total, terrain et frais compris ?\n2. Mon terrain a-t-il un titre foncier ou un document à jour ?\n3. Quelles autorisations faut-il dans ma commune ? Renseignez-vous auprès du service d'urbanisme.\n4. De combien de chambres et de quelle surface ai-je vraiment besoin ?\n5. Qui va construire, et sur la base de quel devis ?"),
        dict(kind="text", nav="27 · Ce que ce guide ne montre pas", title="Il vous aide à choisir. Il ne remplace pas le dossier du modèle.",
             body="Ce guide ne contient pas :\n- les plans de distribution cotés, pièce par pièce ;\n- le devis détaillé du modèle ;\n- la comparaison des modèles entre eux, avec leurs coûts.\n\nCes éléments sont dans le Catalogue Premium WooPlans."),
        dict(kind="catalogue", nav="28 · Page catalogue", title="Vous avez fait le premier pas.", link=link,
             body="Ce guide vous a montré 20 maisons et leur coût de construction estimé. Pour passer de l'idée au projet, il vous faut les plans et les chiffres détaillés.\n\nLe Catalogue Premium WooPlans vous donne :\n- l'accès aux modèles du catalogue ;\n- les plans de distribution cotés ;\n- les devis détaillés ;\n- la possibilité de comparer les modèles et leurs coûts de construction.\n\nPrix actuel : 39 000 FCFA\n\nBouton : Découvrir le Catalogue Premium\nLien : " + link),
        dict(kind="contact", nav="29 · Contact", title="Une question sur votre projet ?",
             body=(f"Écrivez-nous sur WhatsApp : {whatsapp}\nwooplans.com" if whatsapp else "Retrouvez-nous sur wooplans.com")),
    ]
    return P


def check(P: list) -> list:
    out = []
    for p in P:
        pr = guardrails.check_copy(p["title"] + "\n" + p["body"])
        if pr:
            out.append((p["nav"], pr))
    return out


def write_texts(P: list, path: Path) -> None:
    L = ["# Guide : textes des pages", "",
         "Statut : **à relire par Tao**. Titre n°1 retenu, prix du guide 1 900 FCFA. Tous les textes passent `wooplans.guardrails.check_copy`. "
         "Chiffres : catalogue en ligne (`data/plans.json`), arrondis au dixième de million. Fichier généré par `tools/build_guide.py --texts`.", "",
         "Points à confirmer par Tao : (1) le contenu exact du Catalogue Premium listé page 28 ; (2) le numéro WhatsApp page 29 (option `--whatsapp` du script ; sans numéro, la page indique seulement wooplans.com) ; (3) l'affichage des estimations en millions arrondis.", "",
         f"Lien page 28 : `{build_guide_link('page28')}`", ""]
    for p in P:
        L += [f"## {p['nav']}", "", f"**{p['title']}**", "", p["body"], ""]
    path.write_text("\n".join(L), encoding="utf-8")


CSS = """
@font-face{font-family:'Poppins';font-weight:700;src:url('file://%(font)s')}
@page{size:148mm 210mm;margin:0}
*{box-sizing:border-box;margin:0;padding:0}
:root{--g:#0F5B59;--o:#F08A2E;--ink:#1d2b2b;--bg:#faf8f4}
html{font-family:'Inter',sans-serif;color:var(--ink);font-size:10.2pt;line-height:1.5}
.pg{width:148mm;height:210mm;position:relative;overflow:hidden;page-break-after:always;background:var(--bg)}
h1,h2,h3,.big{font-family:'Poppins','Inter',sans-serif;font-weight:700;line-height:1.15}
.foot{position:absolute;left:12mm;right:12mm;bottom:7mm;display:flex;justify-content:space-between;font-size:9pt;color:#6b7a7a}
.cover{background:var(--g)}
.cover .ph{position:absolute;inset:0 0 auto 0;height:128mm;background-size:cover;background-position:center}
.cover .pan{position:absolute;left:0;right:0;bottom:0;height:82mm;background:var(--g);padding:11mm 12mm;color:#fff}
.cover h1{font-size:27pt}.cover .sub{margin-top:4mm;font-size:14pt;color:#f6d3b0}
.cover .bar{width:22mm;height:1.6mm;background:var(--o);margin:5mm 0}
.cover .url{position:absolute;left:12mm;bottom:9mm;font-size:10pt;letter-spacing:.5pt}
.band{background:var(--g);color:#fff;padding:16mm 12mm 10mm}.band h2{font-size:21pt}
.band .bar{width:18mm;height:1.5mm;background:var(--o);margin-top:5mm}
.body{padding:11mm 12mm;font-size:13pt;line-height:1.6}.body p{margin-bottom:5mm}
.body .li{display:flex;gap:3.5mm;margin-bottom:4mm}.body .li b{color:var(--o);min-width:6mm;font-family:Poppins;font-size:15pt}
.toc .card{margin:0 12mm 7mm;font-size:12pt;background:#fff;border-left:2.2mm solid var(--o);padding:7mm 7mm;border-radius:1.5mm;box-shadow:0 .3mm 1.2mm rgba(0,0,0,.08)}
.toc .card b{font-family:Poppins;font-size:15pt;margin-bottom:1.5mm;color:var(--g);display:block}
.div{background:var(--g);color:#fff;display:flex;flex-direction:column;justify-content:center;padding:0 14mm}
.div .badge{font-family:Poppins;font-weight:700;font-size:46pt;color:var(--o);line-height:1}
.div h2{font-size:24pt;margin:7mm 0 5mm}.div p{font-size:14pt;color:#e4efee}
.model .ph{height:84mm;background-size:cover;background-position:center}
.model .in{padding:6mm 12mm}.model h2{font-size:22pt;color:var(--g)}
.chips{display:flex;flex-wrap:wrap;gap:2mm;margin:4mm 0}.chip{background:#e6efee;color:var(--g);border-radius:5mm;padding:1.5mm 3.4mm;font-size:9.4pt;font-weight:600}
.est{background:var(--o);color:#fff;border-radius:2mm;padding:4.5mm 7mm;margin:3mm 0 5mm}
.est small{display:block;font-size:9.5pt;margin-bottom:1mm;opacity:.95;text-transform:uppercase;letter-spacing:.6pt}
.est b{font-family:Poppins;font-size:19pt}
.model .sent{font-size:12.6pt;line-height:1.55}.model .site{margin-top:4mm;color:#6b7a7a;font-size:10pt}
.cat{background:var(--g);color:#fff}.cat .in{padding:17mm 12mm;font-size:12.6pt}.cat h2{font-size:26pt;color:#fff}
.cat .bar{width:20mm;height:1.6mm;background:var(--o);margin:5mm 0}
.cat p{margin-bottom:4mm;color:#e9f2f1;line-height:1.55}.cat ul{margin:3mm 0 8mm 6mm}.cat li{margin-bottom:3mm}
.price{display:inline-block;background:#fff;color:var(--g);border-radius:2mm;padding:4mm 6mm;font-family:Poppins;font-weight:700;font-size:16pt;margin:2mm 0 8mm}
.btn{display:block;background:var(--o);color:#fff;text-decoration:none;text-align:center;border-radius:2mm;padding:5.5mm;font-family:Poppins;font-weight:700;font-size:14pt}
.cat .u{margin-top:5mm;text-align:center;font-size:10.5pt;color:#cfe3e1}
.contact{display:flex;flex-direction:column;justify-content:center;align-items:center;text-align:center;background:var(--g);color:#fff}
.contact h2{font-size:24pt;padding:0 14mm}.contact p{margin-top:7mm;font-size:15pt}
"""


def esc(s): return html.escape(s)


def render_html(P: list, imgs: dict, whatsapp: str = None) -> str:
    css = CSS % {"font": str(ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf")}
    out = []
    n = 0
    for p in P:
        n += 1
        foot = f'<div class="foot"><span>wooplans.com</span><span>{n}</span></div>'
        k = p["kind"]
        if k == "cover":
            out.append(f'<section class="pg cover"><div class="ph" style="background-image:url(\'{imgs[COVER_CODE]}\')"></div>'
                       f'<div class="pan"><h1>{esc(p["title"])}</h1><div class="bar"></div><div class="sub">20 modèles classés par coût de construction</div>'
                       f'<div class="url">wooplans.com</div></div></section>')
        elif k in ("text", "toc"):
            if k == "toc":
                inner = "".join(f'<div class="card"><b>{esc(l.split(" : ")[0])}</b>{esc(l.split(" : ", 1)[1])}</div>' for l in p["body"].split("\n"))
                out.append(f'<section class="pg toc"><div class="band"><h2>{esc(p["title"])}</h2><div class="bar"></div></div><div style="height:9mm"></div>{inner}{foot}</section>')
            else:
                inner = ""
                for para in p["body"].split("\n\n"):
                    lines = para.split("\n")
                    if len(lines) > 1 or lines[0][:2] in ("1.", "- "):
                        for l in lines:
                            if l[:2] == "- ":
                                inner += f'<div class="li"><b>•</b><span>{esc(l[2:])}</span></div>'
                            elif l[:1].isdigit() and l[1:3] == ". ":
                                inner += f'<div class="li"><b>{l[0]}</b><span>{esc(l[3:])}</span></div>'
                            else:
                                inner += f"<p>{esc(l)}</p>"
                    else:
                        inner += f"<p>{esc(para)}</p>"
                out.append(f'<section class="pg"><div class="band"><h2>{esc(p["title"])}</h2><div class="bar"></div></div><div class="body">{inner}</div>{foot}</section>')
        elif k == "divider":
            sub = "<br>".join(esc(x) for x in p["body"].split("\n"))
            out.append(f'<section class="pg div"><div class="badge">{esc(p["badge"])}</div><h2>{esc(p["title"])}</h2><p>{sub}</p></section>')
        elif k == "model":
            chips = "".join(f'<span class="chip">{esc(c)}</span>' for c in p["chips"])
            out.append(f'<section class="pg model"><div class="ph" style="background-image:url(\'{imgs[p["code"]]}\')"></div><div class="in"><h2>{esc(p["title"])}</h2>'
                       f'<div class="chips">{chips}</div><div class="est"><small>Estimation du devis</small><b>{esc(p["estimate"])}</b></div>'
                       f'<p class="sent">{esc(p["sentence"])}</p><p class="site">Retrouvez ce modèle sur wooplans.com</p></div>{foot}</section>')
        elif k == "catalogue":
            lis = "".join(f"<li>{esc(l[2:])}</li>" for l in p["body"].split("\n") if l.startswith("- "))
            out.append(f'<section class="pg cat"><div class="in"><h2>{esc(p["title"])}</h2><div class="bar"></div>'
                       f'<p>Ce guide vous a montré 20 maisons et leur coût de construction estimé. Pour passer de l\'idée au projet, il vous faut les plans et les chiffres détaillés.</p>'
                       f'<p><b>Le Catalogue Premium WooPlans vous donne :</b></p><ul>{lis}</ul><div class="price">Prix actuel : 39 000 FCFA</div>'
                       f'<a class="btn" href="{esc(p["link"])}">Découvrir le Catalogue Premium</a><div class="u">wooplans.com/catalogue-premium</div></div></section>')
        elif k == "contact":
            out.append(f'<section class="pg contact"><h2>{esc(p["title"])}</h2><p>{esc(p["body"]).replace(chr(10), "<br>")}</p></section>')
    return f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{esc(TITLE)}</title><style>{css}</style></head><body>{''.join(out)}</body></html>"


def prepare_images(src: Path, out: Path, codes: list) -> dict:
    out.mkdir(parents=True, exist_ok=True)
    imgs = {}
    for c in codes:
        f = next(iter(sorted(src.glob(f"{c}.*"))), None)
        if f is None:
            raise SystemExit(f"original manquant : {c} dans {src}")
        dest = out / f"{c}.jpg"
        dest.write_bytes(prepare_image(f.read_bytes(), watermark=True, max_side=1400))
        imgs[c] = dest.name
    return imgs


PDF_JS = """const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage();
await p.goto('file://'+process.argv[2]);await p.waitForLoadState('networkidle');
await p.pdf({path:process.argv[3],width:'148mm',height:'210mm',printBackground:true,preferCSSPageSize:true});await b.close();})()"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--src")
    ap.add_argument("--out", default=str(ROOT / "guide" / "out"))
    ap.add_argument("--whatsapp")
    ap.add_argument("--texts", action="store_true")
    a = ap.parse_args()
    plans = {p["code"]: p for p in json.load(open(ROOT / "data" / "plans.json"))}
    P = pages(plans, a.whatsapp)
    bad = check(P)
    if bad:
        raise SystemExit(f"check_copy : {bad}")
    if a.texts:
        write_texts(P, ROOT / "guide" / "TEXTES.md")
        print("TEXTES.md régénéré,", len(P), "pages")
        return
    if not a.src:
        raise SystemExit("--src requis (dossier des originaux)")
    out = Path(a.out)
    codes = [c for *_, cs in TRANCHES for c in cs]
    imgs = prepare_images(Path(a.src), out / "img", codes)
    imgs = {c: f"img/{n}" for c, n in imgs.items()}
    (out / "guide.html").write_text(render_html(P, imgs, a.whatsapp), encoding="utf-8")
    js = out / "_pdf.js"
    js.write_text(PDF_JS)
    pdf = out / "guide_budget.pdf"
    subprocess.run(["node", str(js), str((out / "guide.html").resolve()), str(pdf.resolve())], check=True,
                   env={**__import__("os").environ, "NODE_PATH": "/opt/node22/lib/node_modules"})
    js.unlink()
    print("PDF :", pdf, f"{pdf.stat().st_size / 1e6:.1f} Mo,", len(P), "pages")


if __name__ == "__main__":
    main()
