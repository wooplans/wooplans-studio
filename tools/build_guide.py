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
             + "\nLe Catalogue Premium : près de 100 modèles, avec plan de distribution et devis de la fondation aux finitions, pages 29 et 30"),
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
    P += [
        dict(kind="cat1", nav="29 · Le catalogue", title="Nous avons réuni près de 100 modèles de plans dans un catalogue.", lots=lots,
             body=("Le Catalogue Premium WooPlans.\nPour chacun de ces modèles, vous pouvez consulter le plan de distribution et le devis, de la fondation jusqu'aux finitions.\n\n"
                   "Exemple avec le Duplex D4-006 :\n- le plan de distribution du rez-de-chaussée, avec ses dimensions ;\n- le plan de distribution de l'étage ;\n"
                   "- le devis par lots : " + ", ".join(l[0].lower() for l in lots) + ".\n\nLes plans et les montants complets sont dans le Catalogue Premium.")),
        dict(kind="cat2", nav="30 · Catalogue Premium", title="Le Catalogue Premium WooPlans", link=link,
             body=("Près de 100 modèles de villas et de duplex.\nPour chacun : le plan de distribution et le devis, de la fondation aux finitions.\n\n"
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
.c1 h2{font-size:17pt}.c1 .top p{margin-top:3mm;font-size:10.6pt;color:#e4efee;line-height:1.5}.c1 .top b{color:#fff}
.ex{margin:3.5mm 12mm 0;font-family:Poppins;font-weight:700;font-size:9.5pt;color:var(--o);letter-spacing:.6pt;text-transform:uppercase}
.plans{display:flex;gap:4mm;padding:2mm 12mm 0}.plans figure{flex:1;background:#fff;border:.3mm solid #d8dede;border-radius:1.5mm;padding:2mm;text-align:center}
.plans img{width:100%;height:35mm;object-fit:contain}.plans figcaption{font-size:8pt;font-weight:600;color:var(--g);margin-top:1mm}
.devis{margin:3.5mm 12mm 0;background:#fff;border-radius:1.5mm;padding:3mm 5mm;box-shadow:0 .3mm 1.2mm rgba(0,0,0,.08)}
.devis h3{font-size:10.5pt;color:var(--g);margin-bottom:2mm}
.lot{display:flex;align-items:center;gap:2.5mm;font-size:8.8pt;padding:.75mm 0;border-bottom:.2mm solid #eef1f1}.lot i{font-style:normal;font-family:Poppins;font-weight:700;color:var(--o);width:5mm;font-size:9pt}.lot span{flex:1}.lot b{color:var(--g)}
.mask{display:inline-block;width:24mm;height:2.6mm;background:linear-gradient(90deg,#c9d3d3,#e6ecec);border-radius:1mm}
.devis .note{margin-top:2.2mm;font-size:8pt;color:#8a4a0f;text-align:center}
.c2{background:radial-gradient(ellipse at 50% 28%,#13706d 0,var(--g) 62%);color:#fff}.c2 .bookbox{height:112mm;display:flex;justify-content:center;align-items:center;padding:8mm 0 2mm}.c2 .bookbox img{max-height:100mm;max-width:118mm}
.c2 .in{padding:0 12mm;text-align:center}.c2 h2{font-size:21pt;color:#fff}.c2 .bar{width:20mm;height:1.6mm;background:var(--o);margin:3mm auto}
.c2 .lead{font-size:11.2pt;color:#e4efee;line-height:1.5;margin-bottom:4mm}
.price{display:inline-block;background:#fff;color:var(--g);border-radius:2mm;padding:2.6mm 6mm;font-family:Poppins;font-weight:700;font-size:14pt;margin:0 0 4mm}
.btn{display:block;background:var(--o);color:#fff;text-decoration:none;text-align:center;border-radius:2mm;padding:4.6mm;font-family:Poppins;font-weight:700;font-size:13.5pt}
.c2 .u{margin-top:2.6mm;text-align:center;font-size:9.5pt;color:#cfe3e1}
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
                inner = "".join(f'<div class="card{" next" if l.startswith("Le Catalogue") else ""}"><b>{esc(l.split(" : ")[0])}</b>{esc(l.split(" : ", 1)[1])}</div>' for l in p["body"].split("\n"))
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
            lots = "".join(f'<div class="lot"><i>{n}</i><span>{esc(l)}</span>' + (f'<b>{a:,} FCFA</b>'.replace(",", " ") if a else '<em class="mask"></em>') + "</div>" for n, (l, a) in enumerate(p["lots"], 1))
            out.append(f'<section class="pg c1"><div class="top"><span class="tag">LE CATALOGUE</span><h2>{esc(p["title"])}</h2>'
                       f'<p>Pour chacun de ces modèles, vous pouvez consulter <b>le plan de distribution</b> et <b>le devis, de la fondation jusqu\'aux finitions</b>.</p></div>'
                       f'<div class="ex">Exemple : Duplex D4-006</div>'
                       f'<div class="plans"><figure><img src="{imgs["plan_rdc"]}"><figcaption>Plan de distribution · RDC</figcaption></figure>'
                       f'<figure><img src="{imgs["plan_etage"]}"><figcaption>Plan de distribution · étage</figcaption></figure></div>'
                       f'<div class="devis"><h3>Devis par lots, de la fondation aux finitions</h3>{lots}<div class="note">🔒 Plans lisibles et montants complets dans le Catalogue Premium</div></div>{foot}</section>')
        elif k == "cat2":
            out.append(f'<section class="pg c2"><div class="bookbox"><img src="{imgs["book"]}"></div><div class="in"><h2>{esc(p["title"])}</h2><div class="bar"></div>'
                       f'<p class="lead">Près de 100 modèles de villas et de duplex.<br>Pour chacun : le plan de distribution et le devis, de la fondation aux finitions.</p>'
                       f'<div class="price">Prix actuel : 39 000 FCFA</div>'
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


BOOK_HTML = r'''<!doctype html><html><head><meta charset="utf-8"><style>
@font-face{font-family:'Poppins';font-weight:700;src:url('%FONT%')}
*{margin:0;padding:0;box-sizing:border-box}
html,body{background:transparent;width:1000px;height:820px;font-family:'Inter',sans-serif}
.scene{width:1000px;height:820px;perspective:2400px;position:relative}
.shadow{position:absolute;left:230px;top:650px;width:600px;height:70px;background:radial-gradient(ellipse at center,rgba(0,0,0,.55),rgba(0,0,0,0) 70%);filter:blur(10px)}
.book{position:absolute;left:290px;top:120px;width:380px;height:540px;transform-style:preserve-3d;transform:rotateX(-7deg) rotateY(26deg)}
.face{position:absolute;backface-visibility:hidden}
.front{inset:0;transform:translateZ(30px);background:#0F5B59;border-radius:3px 8px 8px 3px;overflow:hidden;box-shadow:inset 6px 0 10px rgba(0,0,0,.25)}
.front .photo{position:absolute;left:0;right:0;top:212px;height:170px;background:url(cover.jpg) center/cover}
.front .top{position:absolute;left:0;right:0;top:0;height:150px;padding:30px 30px 0;color:#fff}
.front .logo{width:92px;height:auto;display:block;opacity:.95}
.front .kick{margin-top:20px;font-family:Poppins;font-weight:700;font-size:12.5px;letter-spacing:3px;color:#F08A2E}
.front .title{margin-top:6px;font-family:Poppins;font-weight:700;font-size:38px;line-height:1.02;color:#fff}
.front .bot{position:absolute;left:0;right:0;top:382px;bottom:0;padding:18px 30px;color:#fff}
.front .bot .sub{font-size:14.5px;line-height:1.4;color:#e4efee}
.front .bot .badge{position:absolute;right:26px;bottom:20px;background:#F08A2E;color:#fff;font-family:Poppins;font-weight:700;font-size:13px;padding:7px 12px;border-radius:4px}
.front .bot .url{position:absolute;left:30px;bottom:24px;font-size:13px;letter-spacing:.6px;color:#cfe3e1}
.front:after{content:'';position:absolute;inset:0;background:linear-gradient(105deg,rgba(255,255,255,.14) 0,rgba(255,255,255,0) 22%,rgba(0,0,0,0) 70%,rgba(0,0,0,.18));pointer-events:none}
.back{inset:0;transform:translateZ(-30px) rotateY(180deg);background:#0b4a48}
.spine{left:-30px;top:0;width:60px;height:540px;transform:rotateY(-90deg);background:linear-gradient(90deg,#0a4745,#0F5B59 40%,#0c504e);border-radius:3px 0 0 3px;display:flex;align-items:center;justify-content:center}
.spine span{transform:rotate(90deg);white-space:nowrap;font-family:Poppins;font-weight:700;font-size:15px;letter-spacing:2px;color:#fff}
.spine i{position:absolute;left:0;right:0;top:34px;height:3px;background:#F08A2E}
.pages{right:-30px;top:6px;width:60px;height:528px;transform:rotateY(90deg);background:repeating-linear-gradient(90deg,#fbfaf7 0 2px,#e4e1d8 2px 3px)}
.topf{left:0;top:-30px;width:380px;height:60px;transform:rotateX(90deg);background:repeating-linear-gradient(0deg,#fbfaf7 0 2px,#e4e1d8 2px 3px)}
.botf{left:0;bottom:-30px;width:380px;height:60px;transform:rotateX(-90deg);background:#d9d6cc}
</style></head><body><div class="scene"><div class="shadow"></div>
<div class="book">
<div class="face back"></div><div class="face pages"></div><div class="face topf"></div><div class="face botf"></div>
<div class="face spine"><i></i><span>CATALOGUE PREMIUM · WOOPLANS</span></div>
<div class="face front"><div class="top"><img class="logo" src="logo.png"><div class="kick">CATALOGUE PREMIUM</div><div class="title">Villas<br>&amp; Duplex</div></div>
<div class="photo"></div><div class="bot"><div class="sub">Plans de distribution et devis,<br>de la fondation aux finitions</div><div class="url">wooplans.com</div><div class="badge">Près de 100 modèles</div></div></div>
</div></div></body></html>
'''

BOOK_JS = """const {chromium}=require('playwright');
(async()=>{const b=await chromium.launch();const p=await b.newPage({viewport:{width:1000,height:820},deviceScaleFactor:2});
await p.goto('file://'+process.argv[2]);await p.waitForLoadState('networkidle');
await p.screenshot({path:process.argv[3],omitBackground:true});await b.close();})()"""


def make_book(out: Path, cover_jpg: Path) -> str:
    """Visuel « livre » du Catalogue Premium (PNG transparent) : couverture dessinée en HTML, rendue en 3D par Chromium."""
    import os
    import shutil
    work = out / "_book"
    work.mkdir(parents=True, exist_ok=True)
    shutil.copy(cover_jpg, work / "cover.jpg")
    shutil.copy(ROOT / "assets" / "brand" / "logo_white.png", work / "logo.png")
    (work / "book.html").write_text(BOOK_HTML.replace("%FONT%", "file://" + str(ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf")), encoding="utf-8")
    (work / "shot.js").write_text(BOOK_JS)
    dest = out / "img" / "book.png"
    subprocess.run(["node", str(work / "shot.js"), str((work / "book.html").resolve()), str(dest.resolve())], check=True,
                   env={**os.environ, "NODE_PATH": "/opt/node22/lib/node_modules"})
    shutil.rmtree(work)
    from PIL import Image
    im = Image.open(dest)
    box = im.getchannel("A").point(lambda v: 255 if v > 24 else 0).getbbox()
    pad = 24
    im.crop((max(0, box[0] - pad), max(0, box[1] - pad), min(im.width, box[2] + pad), min(im.height, box[3] + pad))).save(dest)
    return "img/book.png"


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
    imgs["book"] = make_book(out, out / "img" / "D5-018.jpg")
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
