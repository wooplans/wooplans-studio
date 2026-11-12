"""Catalogue A3 « modèle A » : génère le PDF A3 (couverture, sommaire, parties Duplex et Villa, pages numérotées)
à partir des données du site wooplans.com. Procédure : catalogue_a3/README.md.

Usage :
  python tools/catalogue_a3.py sync-public [--discover] [--codes D4-004,V4-002]   # champs publics du site (sans secret)
  python tools/catalogue_a3.py ingest <fichier.json|->                            # champs Premium (connecteur wooplans)
  python tools/catalogue_a3.py build [--part all|duplex|villa] [--out f.pdf] [--include-incomplete]
  python tools/catalogue_a3.py check [--strict]                                   # instantanés à jour avec le site ?

Le PDF est écrit dans catalogue_a3/out/ (non versionné). Rien n'est publié ni envoyé : c'est un fichier à relire par Tao.
"""
import argparse
import json
import os
import sys
import time
from datetime import date
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from wooplans import catalogue_a3 as C  # noqa: E402

UA = {"User-Agent": "Mozilla/5.0 (compatible; WooPlansStudio/1.0)"}

FIT_JS = """() => {
  const out = [];
  for (const pg of document.querySelectorAll('.page.model')) {
    for (const sel of ['.col1', '.col3']) {
      const el = pg.querySelector(sel); if (!el) continue;
      let z = 1;
      while (el.scrollHeight > el.clientHeight + 1 && z > 0.7) { z = Math.round((z - 0.03) * 100) / 100; el.style.zoom = z; }
      if (z < 1) out.push({code: pg.dataset.code, col: sel, zoom: z, overflow: el.scrollHeight > el.clientHeight + 1});
    }
  }
  return out;
}"""


def get(url: str, tries: int = 3) -> requests.Response:
    for i in range(tries):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            r.raise_for_status()
            return r
        except requests.RequestException:
            if i == tries - 1:
                raise
            time.sleep(1.5 * (i + 1))


# ---------------------------------------------------------------- sync-public

def cmd_sync_public(args) -> int:
    snaps = C.load_all()
    if args.discover:
        for it in C.parse_sitemap(get(f"{C.SITE}/sitemap.xml").text):
            if it["code"] not in snaps:
                snaps[it["code"]] = {**it}
                print(f"+ nouveau modèle : {it['code']}")
    codes = [c.strip().upper() for c in args.codes.split(",")] if args.codes else sorted(snaps)
    changed = failed = 0
    for code in codes:
        snap = snaps.get(code)
        if not snap or not snap.get("slug"):
            print(f"! {code} : inconnu (utiliser --discover)")
            failed += 1
            continue
        try:
            page = C.parse_public_page(get(f"{C.SITE}/catalogue/{snap['slug']}").text, code)
        except requests.RequestException as e:
            print(f"! {code} : page illisible ({e})")
            failed += 1
            continue
        if not page:
            print(f"! {code} : la fiche publique n'a pas la forme attendue")
            failed += 1
            continue
        before = json.dumps(snap, sort_keys=True)
        C.apply_public(snap, page)
        C.save_snapshot(snap)
        if json.dumps(snap, sort_keys=True) != before:
            changed += 1
            print(f"~ {code} mis à jour")
    print(f"{len(codes)} modèles lus, {changed} mis à jour, {failed} en échec")
    return 1 if failed else 0


# ---------------------------------------------------------------- ingest (champs Premium)

def cmd_ingest(args) -> int:
    raw = sys.stdin.read() if args.file == "-" else Path(args.file).read_text(encoding="utf-8")
    raw = raw.strip()
    try:
        data = json.loads(raw)
        items = data if isinstance(data, list) else [data]
    except json.JSONDecodeError:                       # JSON-lignes
        items = [json.loads(l) for l in raw.splitlines() if l.strip()]
    snaps = C.load_all()
    for it in items:
        snap = C.ingest_payload(it, snaps.get(it["code"]))
        snaps[it["code"]] = snap
        C.save_snapshot(snap)
        got = sum(l["amount"] for l in snap["estimate_lots"])
        if got != snap["estimate_total"]:
            print(f"! {it['code']} : somme des lots {got} ≠ total {snap['estimate_total']}")
    print(f"{len(items)} modèles importés (devis, plans, descriptif)")
    return 0


# ---------------------------------------------------------------- build

def fetch_renders(models: list) -> None:
    """Télécharge dans catalogue_a3/cache/ les rendus publics utilisés (aucun secret)."""
    for m in models:
        by_name = {p.rsplit("/", 1)[-1]: p for p in (m["snap"].get("renders") or [])}
        for path in m["renders"]:
            if path.exists() or path.name not in by_name:
                continue
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(get(C.SITE + by_name[path.name]).content)


def as_jpeg(p: Path, code: str, quality: int = 90) -> Path:
    """Chromium recopie les JPEG tels quels dans le PDF, mais ré-encode WebP et PNG sans perte (PDF 5 à 10 fois plus lourd)."""
    if p.suffix.lower() in (".jpg", ".jpeg"):
        return p
    dst = C.CACHE / "jpg" / code / (p.stem + ".jpg")
    if not dst.exists() or dst.stat().st_mtime < p.stat().st_mtime:
        from PIL import Image
        dst.parent.mkdir(parents=True, exist_ok=True)
        Image.open(p).convert("RGB").save(dst, "JPEG", quality=quality, optimize=True)
    return dst


def render_pdf(html_path: Path, pdf_path: Path) -> list:
    """1) Playwright ouvre la page et resserre le texte des colonnes qui débordent (zoom) ; 2) le HTML ajusté est écrit
    à côté ; 3) Chromium imprime ce HTML en PDF directement sur disque (le pilote Playwright manque de mémoire au-delà
    d'une centaine de pages : il ne sert donc pas à produire le PDF)."""
    import subprocess
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        exe = os.environ.get("CHROMIUM_PATH") or p.chromium.executable_path
        browser = p.chromium.launch(executable_path=exe, args=["--no-sandbox", "--allow-file-access-from-files"])
        page = browser.new_page(viewport={"width": 1588, "height": 1123})
        page.goto(html_path.resolve().as_uri(), wait_until="load")
        page.wait_for_function("[...document.images].every(i => i.complete)", timeout=180000)
        page.evaluate("document.fonts.ready")
        fit = page.evaluate(FIT_JS)
        final = html_path.with_name(html_path.stem + ".final.html")
        final.write_text(page.content(), encoding="utf-8")
        browser.close()
    cmd = [exe, "--headless=new", "--no-sandbox", "--disable-gpu", "--allow-file-access-from-files", "--no-pdf-header-footer",
           "--generate-pdf-document-outline", f"--print-to-pdf={pdf_path}", final.resolve().as_uri()]
    r = subprocess.run(cmd, capture_output=True, text=True, timeout=900)
    if not pdf_path.exists() or pdf_path.stat().st_size < 10000:
        raise RuntimeError(f"Chromium n'a pas produit le PDF : {r.stderr[-400:]}")
    return fit


def plan_warnings(models: list) -> list:
    """Anomalies de plans à corriger sur le site : même fichier sur deux modèles, plan trop petit pour une impression A3."""
    import hashlib
    from PIL import Image
    seen, out = {}, []
    for m in models:
        code = m["snap"]["code"]
        for p in m["plans"]:
            seen.setdefault(hashlib.md5(p.read_bytes()).hexdigest(), []).append(code)
            try:
                w, h = Image.open(p).size
            except Exception:
                out.append((code, f"plan illisible : {p.name}"))
                continue
            if min(w, h) < 600:
                out.append((code, f"plan basse résolution ({w} × {h} px) : {p.name}"))
    out += [(" / ".join(sorted(set(v))), "même fichier de plan sur plusieurs modèles : un des deux est faux") for v in seen.values() if len(set(v)) > 1]
    return out


def cmd_build(args) -> int:
    snaps, overrides = C.load_all(), C.load_overrides()
    models, excluded = [], []
    for code in sorted(snaps):
        s = snaps[code]
        if args.part != "all" and s.get("category") != args.part:
            continue
        m = C.model_data(s, overrides)
        miss = C.missing_data(s, m["plans"])
        if miss and not args.include_incomplete:
            excluded.append((code, ", ".join(miss)))
        else:
            models.append(m)
    if not models:
        print("Aucun modèle complet : lancer sync-public puis ingest (voir catalogue_a3/README.md)")
        return 1
    fetch_renders(models)
    for m in models:
        m["renders"] = [as_jpeg(p, m["snap"]["code"]) for p in m["renders"]]
    C.OUT.mkdir(parents=True, exist_ok=True)
    logo = C.BASE / "assets" / "logo_white.png"
    doc, lay = C.build_document(models, args.part, date.today(), logo)
    html_path = C.OUT / f"catalogue-a3-{args.part}.html"
    html_path.write_text(doc, encoding="utf-8")
    pdf_path = Path(args.out) if args.out else C.OUT / f"catalogue-a3-{args.part}.pdf"
    fit = render_pdf(html_path, pdf_path)
    problems = [(m["snap"]["code"], p) for m in models for p in C.model_problems(m)]
    lines = [f"# Catalogue A3 : rapport de génération ({date.today().isoformat()}, partie « {args.part} »)", "",
             f"- {sum(1 for _ in models)} modèles dans le document, {lay['total']} pages (couverture, {lay['sommaire_pages']} page(s) de sommaire, séparateurs, fiches).",
             f"- PDF : {pdf_path}", ""]
    if excluded:
        lines += [f"## Modèles non inclus (données manquantes sur le site) : {len(excluded)}", ""] + [f"- {c} : {why}" for c, why in excluded] + [""]
    if problems:
        lines += [f"## Écarts à relire : {len(problems)}", ""] + [f"- {c} : {p}" for c, p in problems] + [""]
    skipped = [(c, ov["note"]) for c, ov in sorted(overrides.items()) if ov.get("skip_plans") and any(m["snap"]["code"] == c for m in models)]
    if skipped:
        lines += [f"## Fichiers de plan écartés (ce ne sont pas des plans) : {len(skipped)}", ""] + [f"- {c} : {n}" for c, n in skipped] + [""]
    warn = plan_warnings(models)
    if warn:
        lines += [f"## Plans à vérifier sur le site : {len(warn)}", ""] + [f"- {c} : {w}" for c, w in warn] + [""]
    if fit:
        lines += [f"## Mise en page resserrée (texte réduit pour tenir sur la page) : {len(fit)}", ""] + [
            f"- {f['code']} {f['col']} : zoom {f['zoom']}{' (déborde encore)' if f['overflow'] else ''}" for f in fit] + [""]
    (C.OUT / f"RAPPORT-{args.part}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))
    return 0


# ---------------------------------------------------------------- check

def cmd_check(args) -> int:
    snaps = C.load_all()
    site = {i["code"]: i for i in C.parse_sitemap(get(f"{C.SITE}/sitemap.xml").text)}
    stale = [f"{c} : sur le site, absent des instantanés" for c in sorted(set(site) - set(snaps))]
    stale += [f"{c} : retiré du site (toujours dans les instantanés)" for c in sorted(set(snaps) - set(site))]
    for code in sorted(set(snaps) & set(site)):
        page = C.parse_public_page(get(f"{C.SITE}/catalogue/{snaps[code]['slug']}").text, code)
        diff = [k for k in C.PUBLIC_FIELDS if k in page and snaps[code].get(k) != page[k]]
        if diff:
            stale.append(f"{code} : champs changés sur le site : {', '.join(diff)}")
    print("\n".join(stale) if stale else "Instantanés à jour avec le site (champs publics).")
    print("Rappel : devis, plans et descriptif (Premium) se resynchronisent avec le connecteur wooplans (ingest).")
    return 1 if (stale and args.strict) else 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("sync-public")
    p.add_argument("--discover", action="store_true")
    p.add_argument("--codes")
    p.set_defaults(fn=cmd_sync_public)
    p = sub.add_parser("ingest")
    p.add_argument("file")
    p.set_defaults(fn=cmd_ingest)
    p = sub.add_parser("build")
    p.add_argument("--part", choices=["all", "duplex", "villa"], default="all")
    p.add_argument("--out")
    p.add_argument("--include-incomplete", action="store_true")
    p.set_defaults(fn=cmd_build)
    p = sub.add_parser("check")
    p.add_argument("--strict", action="store_true")
    p.set_defaults(fn=cmd_check)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
