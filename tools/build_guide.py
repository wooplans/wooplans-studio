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
COMPARE_CODES = ["V4-010", "D4-006", "D4-003"]
# Devis par lots du Duplex D4-006 (catalogue en ligne) : seule la ligne « Fondation » est montrée avec son montant, le reste est masqué.
LOTS_EXEMPLE = [("Fondation", 3601300), ("Élévation RDC", None), ("Dalle", None), ("Élévation étage", None), ("Charpente et toiture", None),
                ("Crépissage et antivols", None), ("Portes et fenêtres", None), ("Plomberie et électricité", None), ("Plafond et peinture", None), ("Carrelage", None)]


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
             body="\n".join(f"{t} : {len(c)} modèles, de {rng(c)[0]} à {rng(c)[1]} millions FCFA" for t, _, _, c in TRANCHES)
             + "\nÉtape suivante : plans cotés et devis détaillés dans le Catalogue Premium, pages 29 et 30"),
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
    lots = LOTS_EXEMPLE
    cmp_rows = [plans[c] for c in COMPARE_CODES]
    cmp_txt = "\n".join(f"{r['code']} : {r['bedrooms']} chambres · {r['surface']} m² · terrain {r['land_area']} m² · environ {millions(r['estimate_total'])} millions FCFA" for r in cmp_rows)
    P += [
        dict(kind="cat1", nav="29 · Fin du guide, étape suivante", title="Vous avez repéré vos modèles. Voici l'étape suivante.", lots=lots, cmp=cmp_rows,
             body=("Fin du guide.\nUne fois le modèle choisi, il vous faut le dossier complet. Exemple avec le Duplex D4-006 :\n"
                   "- le plan de distribution du rez-de-chaussée, avec ses dimensions ;\n- le plan de distribution de l'étage ;\n"
                   "- le devis détaillé par lots : " + ", ".join(l[0].lower() for l in lots[:5]) + "… ;\n"
                   "Les plans et les montants complets sont dans le Catalogue Premium.\n\n"
                   "Comparer des modèles du guide, côte à côte :\n" + cmp_txt)),
        dict(kind="cat2", nav="30 · Catalogue Premium", title="Catalogue Premium WooPlans", link=link,
             body=("Du choix de la maison au dossier complet.\n\nLe Catalogue Premium WooPlans vous donne :\n"
                   "- les plans de distribution cotés, niveau par niveau ;\n"
                   "- le devis détaillé par lots (fondation, dalle, charpente et toiture, plomberie et électricité, carrelage…) ;\n"
                   "- la comparaison des modèles et de leurs coûts de construction ;\n- l'accès aux modèles du catalogue.\n\n"
                   "Prix actuel : 39 000 FCFA\n\nBouton : Découvrir le Catalogue Premium\nLien : " + link)),
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
.toc .card{margin:0 12mm 4.5mm;font-size:10.6pt;background:#fff;border-left:2.2mm solid var(--o);padding:4.6mm 6mm;border-radius:1.5mm;box-shadow:0 .3mm 1.2mm rgba(0,0,0,.08)}
.toc .card b{font-family:Poppins;font-size:12.8pt;margin-bottom:1mm;color:var(--g);display:block}
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
.toc .card.next{background:var(--g);color:#fff;border-left-color:var(--o)}.toc .card.next b{color:#fff}
.c1{background:var(--bg)}.c1 .top{background:var(--g);color:#fff;padding:8mm 12mm 5mm}
.tag{display:inline-block;background:var(--o);color:#fff;font-family:Poppins;font-weight:700;font-size:8.5pt;letter-spacing:1pt;padding:1.2mm 3mm;border-radius:1mm;margin-bottom:3mm}
.c1 h2{font-size:17.5pt}.c1 .top p{margin-top:2.5mm;font-size:10.5pt;color:#e4efee;line-height:1.45}
.plans{display:flex;gap:4mm;padding:3.5mm 12mm 0}.plans figure{flex:1;background:#fff;border:.3mm solid #d8dede;border-radius:1.5mm;padding:2mm;text-align:center}
.plans img{width:100%;height:33mm;object-fit:contain}.plans figcaption{font-size:8pt;font-weight:600;color:var(--g);margin-top:1mm}
.lock{margin:2.5mm 12mm 0;background:#fff3e6;border:.3mm dashed var(--o);color:#8a4a0f;border-radius:1.5mm;padding:2mm 3mm;font-size:8.8pt;font-weight:600;text-align:center}
.devis{margin:3mm 12mm 0;background:#fff;border-radius:1.5mm;padding:3mm 5mm;box-shadow:0 .3mm 1.2mm rgba(0,0,0,.08)}
.devis h3,.cmp h3{font-size:10.5pt;color:var(--g);margin-bottom:2mm}
.lots{display:grid;grid-template-columns:1fr 1fr;column-gap:6mm}.lot{display:flex;justify-content:space-between;align-items:center;font-size:8.2pt;padding:.8mm 0;border-bottom:.2mm solid #eef1f1}.lot b{color:var(--g)}
.mask{display:inline-block;width:13mm;height:2.6mm;background:linear-gradient(90deg,#c9d3d3,#e6ecec);border-radius:1mm}
.devis .note{margin-top:1.8mm;font-size:7.8pt;color:#6b7a7a;text-align:right}
.cmp{margin:3mm 12mm 0}.cmp table{width:100%;border-collapse:collapse;font-size:8.8pt;background:#fff}.cmp td{padding:1.1mm 2mm;border-bottom:.2mm solid #eef1f1}.cmp td.e{color:var(--o);font-weight:700;text-align:right}.cmp td b{color:var(--g)}
.c2{background:var(--g);color:#fff}.c2 .strip{display:flex;height:50mm}.c2 .strip div{flex:1;background-size:cover;background-position:center;border-right:.8mm solid var(--g)}
.c2 .in{padding:8mm 12mm}.c2 h2{font-size:23pt;color:#fff}.c2 .bar{width:20mm;height:1.6mm;background:var(--o);margin:4mm 0}
.c2 .lead{font-size:12pt;color:#e4efee;margin-bottom:5mm}
.c2 .row{display:flex;gap:4mm;align-items:flex-start;margin-bottom:3.2mm}.c2 .ic{background:#fff;border-radius:2mm;width:10mm;height:10mm;display:flex;align-items:center;justify-content:center;font-size:13pt;flex:none}
.c2 .row b{display:block;font-size:11.5pt}.c2 .row small{display:block;font-size:9.2pt;color:#cfe3e1;line-height:1.35}
.price{display:inline-block;background:#fff;color:var(--g);border-radius:2mm;padding:3mm 6mm;font-family:Poppins;font-weight:700;font-size:15pt;margin:2mm 0 5mm}
.btn{display:block;background:var(--o);color:#fff;text-decoration:none;text-align:center;border-radius:2mm;padding:5mm;font-family:Poppins;font-weight:700;font-size:14pt}
.c2 .u{margin-top:3mm;text-align:center;font-size:10pt;color:#cfe3e1}
"""


def esc(s): return html.escape(s)


def render_html(P: list, imgs: dict, whatsapp: str = None) -> str:
    css = CSS.replace("%(font)s", str(ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf"))
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
                inner = "".join(f'<div class="card{" next" if l.startswith("Étape") else ""}"><b>{esc(l.split(" : ")[0])}</b>{esc(l.split(" : ", 1)[1])}</div>' for l in p["body"].split("\n"))
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
        elif k == "cat1":
            lots = "".join(f'<div class="lot"><span>{esc(l)}</span>' + (f'<b>{a:,} FCFA</b>'.replace(",", " ") if a else '<i class="mask"></i>') + "</div>" for l, a in p["lots"])
            rows = "".join(f'<tr><td><b>{esc(r["code"])}</b></td><td>{r["bedrooms"]} ch.</td><td>{r["surface"]} m²</td><td>{r["land_area"]} m²</td><td class="e">{millions(r["estimate_total"])} M</td></tr>' for r in p["cmp"])
            out.append(f'<section class="pg c1"><div class="top"><span class="tag">FIN DU GUIDE</span><h2>{esc(p["title"])}</h2>'
                       f'<p>Une fois le modèle choisi, il vous faut le dossier complet. Exemple avec le <b>Duplex D4-006</b> :</p></div>'
                       f'<div class="plans"><figure><img src="{imgs["plan_rdc"]}"><figcaption>Plan de distribution · RDC</figcaption></figure>'
                       f'<figure><img src="{imgs["plan_etage"]}"><figcaption>Plan de distribution · étage</figcaption></figure></div>'
                       f'<div class="lock">🔒 Dimensions et détails lisibles dans le Catalogue Premium</div>'
                       f'<div class="devis"><h3>Devis détaillé par lots</h3><div class="lots">{lots}</div><div class="note">Montants complets dans le Catalogue Premium</div></div>'
                       f'<div class="cmp"><h3>Comparez des modèles du guide, côte à côte</h3><table>{rows}</table></div>{foot}</section>')
        elif k == "cat2":
            lis = [("📐", "Plans de distribution cotés", "niveau par niveau"), ("🧾", "Devis détaillé par lots", "fondation, dalle, charpente et toiture, plomberie et électricité, carrelage…"),
                   ("⚖️", "Comparaison des modèles", "et de leurs coûts de construction"), ("🏠", "Accès aux modèles du catalogue", "villas et duplex")]
            rows = "".join(f'<div class="row"><span class="ic">{i}</span><div><b>{esc(t)}</b><small>{esc(d)}</small></div></div>' for i, t, d in lis)
            strip = "".join(f'<div style="background-image:url(\'{imgs[c]}\')"></div>' for c in ("D4-006", "D5-018", "V4-010"))
            out.append(f'<section class="pg c2"><div class="strip">{strip}</div><div class="in"><h2>{esc(p["title"])}</h2><div class="bar"></div>'
                       f'<p class="lead">Du choix de la maison au dossier complet.</p>{rows}<div class="price">Prix actuel : 39 000 FCFA</div>'
                       f'<a class="btn" href="{esc(p["link"])}">Découvrir le Catalogue Premium</a><div class="u">wooplans.com/catalogue-premium</div></div></section>')
    return f"<!doctype html><html lang='fr'><head><meta charset='utf-8'><title>{esc(TITLE)}</title><style>{css}</style></head><body>{''.join(out)}</body></html>"


def prepare_plans(plans_dir: Path, out: Path) -> dict:
    """Plans de distribution de l'exemple (D4-006) floutés : formes lisibles, cotes illisibles."""
    from PIL import Image, ImageFilter
    res = {}
    for key, name in (("plan_rdc", "rdc"), ("plan_etage", "etage")):
        f = next(iter(sorted(plans_dir.glob(f"{name}.*"))), None)
        if f is None:
            raise SystemExit(f"plan manquant : {name} dans {plans_dir}")
        im = Image.open(f).convert("RGB")
        im.thumbnail((700, 700))
        dest = out / f"{key}.jpg"
        im.filter(ImageFilter.GaussianBlur(4)).save(dest, quality=88)
        res[key] = f"img/{dest.name}"
    return res


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
    ap.add_argument("--plans", help="dossier avec rdc.webp et etage.webp (plans du D4-006, R2 premium)")
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
    if not a.plans:
        raise SystemExit("--plans requis (plans du D4-006)")
    imgs.update(prepare_plans(Path(a.plans), out / "img"))
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
