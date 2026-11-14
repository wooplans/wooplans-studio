"""Visuels des pubs Facebook du guide « Quelle maison construire avec votre budget ? » (3 images 4:5 + 5 cartes de carrousel 1:1).

Usage : python tools/build_ads.py --img DOSSIER_IMAGES_FILIGRANEES [--out guide/pubs]
  DOSSIER_IMAGES : CODE.jpg (rendus réduits et filigranés produits par tools/build_guide.py, dossier out/img)
Chiffres : data/plans.json uniquement. Textes : check_copy (montants autorisés : 1 900 FCFA).
Les rendus sont affichés ENTIERS (cadre 16:9, jamais rognés).
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
from tools.build_guide import TRANCHES, millions  # noqa: E402

PRICE = "1 900 FCFA"
FONT = ROOT / "visite_plan" / "fonts" / "Poppins-Bold.ttf"
CSS = """
@font-face{font-family:'Poppins';font-weight:700;src:url('file://%FONT%')}
*{margin:0;padding:0;box-sizing:border-box}
:root{--g:#0F5B59;--o:#F08A2E;--bg:#FAF8F4;--ink:#1d2b2b}
body{font-family:'Inter',sans-serif;color:var(--ink);width:1080px}
h1,h2,.pop{font-family:'Poppins','Inter',sans-serif;font-weight:700;line-height:1.1}
.a{width:1080px;height:1350px;position:relative;background:var(--g);color:#fff;overflow:hidden}
.sq{width:1080px;height:1080px;position:relative;background:var(--g);color:#fff;overflow:hidden}
.ph{width:1080px;height:608px;background-size:100% 100%}
.tag{display:inline-block;background:var(--o);color:#fff;font-family:Poppins;font-weight:700;font-size:26px;letter-spacing:4px;padding:8px 22px;border-radius:6px}
.price{display:inline-block;background:#fff;color:var(--g);font-family:Poppins;font-weight:700;font-size:44px;padding:14px 34px;border-radius:12px}
.url{font-size:30px;letter-spacing:1px;color:#cfe3e1}
.pad{padding:44px 56px}
.chips{display:flex;flex-wrap:wrap;gap:14px;margin-top:30px}.chip{background:rgba(255,255,255,.14);border:2px solid rgba(255,255,255,.35);border-radius:40px;padding:10px 26px;font-size:30px;font-weight:600}
"""


def esc(s):
    return html.escape(s)


def build(plans: dict, img: Path) -> dict:
    """Retourne {nom_fichier: (html, largeur, hauteur)} et la liste des textes à contrôler."""
    rng = lambda codes: (millions(min(plans[c]["estimate_total"] for c in codes)), millions(max(plans[c]["estimate_total"] for c in codes)))
    im = lambda c: f"file://{(img / (c + '.jpg')).resolve()}"
    ads, texts = {}, []

    # 1 · titre + façade entière
    t1 = ("Quelle maison construire avec votre budget ?", "20 modèles classés par coût de construction")
    texts += list(t1)
    ads["pub1_budget.png"] = (f'<div class="a"><div class="ph" style="background-image:url({im("D4-003")})"></div>'
                              f'<div class="pad" style="padding-top:40px"><span class="tag">GUIDE EN IMAGES</span>'
                              f'<h1 style="font-size:80px;margin:26px 0 20px">{esc(t1[0])}</h1><p style="font-size:42px;color:#e4efee;line-height:1.3">{esc(t1[1])}</p>'
                              f'<div class="chips"><span class="chip">20 modèles</span><span class="chip">4 tranches de budget</span><span class="chip">Estimation du devis</span></div>'
                              f'<div style="position:absolute;left:56px;right:56px;bottom:44px;display:flex;justify-content:space-between;align-items:center">'
                              f'<span class="price">{PRICE}</span><span class="url">wooplans.com</span></div></div></div>', 1080, 1350)

    # 2 · grille de 4 façades entières avec leur estimation
    codes = ["V3-027", "V4-010", "D4-006", "D5-018"]
    t2 = "20 maisons, 20 budgets"
    texts.append(t2)
    tiles = ""
    for c in codes:
        p = plans[c]
        cap = f"{'Villa' if p['category'] == 'villa' else 'Duplex'} {c} · environ {millions(p['estimate_total'])} millions FCFA"
        texts.append(cap)
        tiles += (f'<div style="width:490px"><div style="width:490px;height:276px;background:url({im(c)});background-size:100% 100%;border-radius:10px;box-shadow:0 3px 12px rgba(0,0,0,.3)"></div>'
                  f'<div style="font-size:23px;margin-top:10px;color:#e4efee;line-height:1.25">{esc(cap)}</div></div>')
    ads["pub2_grille.png"] = (f'<div class="a" style="background:var(--g)"><div class="pad" style="padding-bottom:0"><span class="tag">GUIDE EN IMAGES</span>'
                              f'<h1 style="font-size:84px;margin:24px 0 8px">{esc(t2)}</h1><p style="font-size:34px;color:#e4efee">Moins de 20 millions, 20 à 40, 40 à 60, plus de 60</p></div>'
                              f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:34px 20px;padding:40px 50px 0">{tiles}</div>'
                              f'<div style="position:absolute;left:0;right:0;bottom:0;background:#0b4a48;padding:30px 56px;display:flex;justify-content:space-between;align-items:center">'
                              f'<span class="pop" style="font-size:36px">Le guide en images</span><span class="price" style="font-size:40px">{PRICE}</span></div></div>', 1080, 1350)

    # 3 · tranche « moins de 20 millions »
    lo, hi = rng(TRANCHES[0][3])
    t3 = ("Moins de 20 millions FCFA ?", f"5 modèles de villas 3 chambres, de {lo} à {hi} millions FCFA", "Voyez les maisons que vous pouvez envisager")
    texts += list(t3)
    ads["pub3_tranche.png"] = (f'<div class="a"><div class="ph" style="background-image:url({im("V3-025")})"></div>'
                               f'<div class="pad" style="padding-top:40px"><h1 style="font-size:78px;margin:6px 0 20px;color:#fff">{esc(t3[0])}</h1>'
                               f'<p style="font-size:40px;line-height:1.3;color:#ffd9b3;font-weight:600">{esc(t3[1])}</p>'
                               f'<p style="font-size:36px;margin-top:14px;color:#e4efee">{esc(t3[2])}</p>'
                               f'<div class="chips"><span class="chip">Façade</span><span class="chip">Chambres et surface</span><span class="chip">Estimation du devis</span></div>'
                               f'<div style="position:absolute;left:56px;right:56px;bottom:44px;display:flex;justify-content:space-between;align-items:center">'
                               f'<span class="price">Le guide : {PRICE}</span><span class="url">wooplans.com</span></div></div></div>', 1080, 1350)

    # 4 · carrousel : couverture du guide + 4 tranches
    ads["pub4_carte1_guide.png"] = (f'<div class="sq" style="display:flex;align-items:center;justify-content:center;background:#0b4a48">'
                                    f'<img src="file://{(img / "_cover.png").resolve()}" style="height:960px;box-shadow:0 12px 40px rgba(0,0,0,.45);border-radius:6px"></div>', 1080, 1080)
    cards = [("V3-025", 0), ("V5-008", 1), ("D4-007", 2), ("D5-018", 3)]
    for n, (c, i) in enumerate(cards, 2):
        title, _, _, codes = TRANCHES[i]
        lo, hi = rng(codes)
        sub = f"5 modèles · de {lo} à {hi} millions FCFA"
        pl = plans[c]
        cap = f"{'Villa' if pl['category'] == 'villa' else 'Duplex'} {c} · {pl['bedrooms']} chambres · {pl['surface']} m² · environ {millions(pl['estimate_total'])} millions FCFA"
        texts += [title, sub, cap]
        ads[f"pub4_carte{n}_tranche{i + 1}.png"] = (f'<div class="sq"><div class="ph" style="background-image:url({im(c)});height:608px"></div>'
                                                    f'<div class="pad" style="padding-top:36px"><h2 style="font-size:64px;margin-bottom:16px">{esc(title)}</h2>'
                                                    f'<p style="font-size:38px;color:#ffd9b3;font-weight:600">{esc(sub)}</p>'
                                                    f'<p style="font-size:30px;color:#e4efee;margin-top:20px">{esc(cap)}</p></div>'
                                                    f'<div style="position:absolute;left:56px;right:56px;bottom:34px;display:flex;justify-content:space-between;align-items:center">'
                                                    f'<span class="price" style="font-size:36px;padding:10px 26px">Le guide : {PRICE}</span><span class="url" style="font-size:28px">wooplans.com</span></div></div>', 1080, 1080)
    return ads, texts


SHOT_JS = """const {chromium}=require('playwright');const fs=require('fs');
(async()=>{const jobs=JSON.parse(fs.readFileSync(process.argv[2]));const b=await chromium.launch();
for(const j of jobs){const p=await b.newPage({viewport:{width:j.w,height:j.h}});await p.goto('file://'+j.html);await p.waitForLoadState('networkidle');
await p.screenshot({path:j.out,clip:{x:0,y:0,width:j.w,height:j.h}});await p.close();}await b.close();})()"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--img", required=True)
    ap.add_argument("--out", default=str(ROOT / "guide" / "pubs"))
    a = ap.parse_args()
    plans = {p["code"]: p for p in json.load(open(ROOT / "data" / "plans.json"))}
    img, out = Path(a.img), Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    # couverture du guide (page 1 du PDF) pour la 1re carte du carrousel
    subprocess.run(["pdftoppm", "-r", "190", "-f", "1", "-l", "1", "-png", "-singlefile", str(ROOT / "guide" / "guide_budget.pdf"), str(img / "_cover")], check=True)
    ads, texts = build(plans, img)
    bad = [(t, guardrails.check_copy(t, {1900})) for t in texts if guardrails.check_copy(t, {1900})]
    if bad:
        raise SystemExit(f"check_copy : {bad}")
    work = out / "_work"
    work.mkdir(exist_ok=True)
    jobs = []
    for name, (body, w, h) in ads.items():
        f = work / (name + ".html")
        f.write_text(f"<!doctype html><html><head><meta charset='utf-8'><style>{CSS.replace('%FONT%', str(FONT))}</style></head><body>{body}</body></html>", encoding="utf-8")
        jobs.append({"html": str(f.resolve()), "out": str((out / name).resolve()), "w": w, "h": h})
    (work / "jobs.json").write_text(json.dumps(jobs))
    (work / "shot.js").write_text(SHOT_JS)
    import os
    subprocess.run(["node", str(work / "shot.js"), str(work / "jobs.json")], check=True, env={**os.environ, "NODE_PATH": "/opt/node22/lib/node_modules"})
    import shutil
    shutil.rmtree(work)
    print(len(jobs), "visuels dans", out)


if __name__ == "__main__":
    main()
