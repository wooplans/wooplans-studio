"""Catalogue A3 « modèle A » : une fiche A3 par modèle, générée à partir des données du site wooplans.com.

Source des données (décision de Tao, 12 nov.) : le SITE, pas le PDF.
- Champs publics (nom, résumé, chambres, surface, dimensions, terrain, rendus) : lus sur la fiche publique
  https://www.wooplans.com/catalogue/<slug>, sans secret (`sync_public`).
- Champs Premium (descriptif complet, devis par lot, plans de distribution) : servis par le connecteur wooplans
  (voir `ingest` dans tools/catalogue_a3.py).
Le document est découpé en deux parties (Duplex, Villa), avec couverture, sommaire cliquable et pages numérotées.
Ce module ne fait aucun accès réseau : tout ce qui touche au site est dans tools/catalogue_a3.py.
"""
from __future__ import annotations

import html as _html
import json
import math
import os
import re
from datetime import date
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Tuple

SITE = "https://www.wooplans.com"
ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "catalogue_a3"
DATA, PLANS, CACHE, HIRES, OUT, ORIG = (BASE / n for n in ("data", "plans", "cache", "hires", "out", "orig"))
OVERRIDES = BASE / "overrides.json"
CATEGORIES = (("duplex", "Duplex"), ("villa", "Villa"))
NB = " "
ROWS_PER_COL = 44          # entrées du sommaire par colonne
COLS_PER_PAGE = 4          # colonnes du sommaire par page A3
PUBLIC_FIELDS = ("name", "summary", "bedrooms", "bathrooms", "levels", "surface_total",
                 "building_width", "building_depth", "land_area", "land_width", "land_depth", "renders")
DIM_FIELDS = ("building_width", "building_depth", "land_area", "land_width", "land_depth")
CAPTIONS = ("Vue de façade", "Vue extérieure", "Vue d'ensemble")
MOIS = ("janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre")


# ---------------------------------------------------------------- mise en forme du texte

def esc(s) -> str:
    return _html.escape(str(s), quote=True)


def fr_num(x) -> str:
    if x is None:
        return ""
    if isinstance(x, float):
        x = round(x, 2)                       # le site contient des 20.759999999999998
        if x.is_integer():
            x = int(x)
    return str(x).replace(".", ",")


def money(n) -> str:
    return f"{int(n):,}".replace(",", NB)


def fr_date(d: date) -> str:
    return f"{d.day} {MOIS[d.month - 1]} {d.year}"


def norm_text(s: str) -> str:
    """« 01 salon+ salle », « 155,88m2 » → « 1 salon + salle », « 155,88 m² » (texte du site, tel quel sinon)."""
    s = (s or "").replace("\r", "")
    s = re.sub(r"(\d)\s*m2\b", rf"\1{NB}m²", s)
    s = re.sub(r"(\d)\s*m²", rf"\1{NB}m²", s)
    s = re.sub(r"\b0(\d)\b", r"\1", s)
    s = re.sub(r"(\w)\+\s+(\w)", r"\1 + \2", s)
    s = re.sub(r"[ \t]+", " ", s)
    return s.strip()


def intro_paragraph(snap: dict, limit: int = 520) -> str:
    """Descriptif court : début de la description du site (avant « Caractéristiques » / « Gros œuvre »), sinon le résumé."""
    d = snap.get("description") or ""
    cut = re.split(r"\n\s*(?:Caractéristiques|Gros œuvre)\b", d, maxsplit=1)[0]
    text = norm_text(re.sub(r"\s*\n\s*", " ", cut))
    if not text:
        text = norm_text(snap.get("summary") or "")
    if len(text) > limit:
        k = text.rfind(". ", 0, limit)
        text = text[:k + 1] if k > 200 else text[:limit].rsplit(" ", 1)[0] + "…"
    return text


_FEATURE = re.compile(r"^\s*[-•*]\s*(\d+)\s*(\D.*?)\s*$")
_ENGLISH = {"living", "dining", "kitchen", "bedroom", "bedrooms", "bath", "baths", "bathroom", "bathrooms", "office", "store", "laundry",
            "study", "guest", "guest's", "toilet", "dinin", "master's", "master", "cinema", "garage", "terrace", "hall", "corridor", "dressing", "room", "rooms",
            "lounge", "pantry", "balcony", "pool", "gym"}


def _pluriel(n: int, label: str) -> str:
    """« 5 salle de bain » → « 5 salles de bain » (pluriel simple du premier mot ; non touché si déjà au pluriel)."""
    parts = label.split()
    if n < 2 or not parts or parts[0].isupper() or parts[0][-1:] in "sxz":
        return label
    parts[0] += "s"
    if len(parts) > 1 and parts[1] in ("principale", "secondaire", "parentale"):
        parts[1] += "s"
    return " ".join(parts)


def parse_features(description: str, limit: int = 12) -> List[str]:
    """Liste « Caractéristiques » de la description du site : « 02 Living (02 Salons) » → « 2 salons » ;
    « 01 Chambre (Visiteur) » reste « 1 chambre (visiteur) » (le français principal n'est pas remplacé)."""
    m = re.search(r"Caractéristiques\s*:?(.*?)(?:\n\s*Gros œuvre|\Z)", description or "", re.S | re.I)
    if not m:
        return []
    out: List[str] = []
    for line in m.group(1).splitlines():
        fm = _FEATURE.match(line)
        if not fm:
            continue
        n, rest = int(fm.group(1)), fm.group(2)
        pm = re.match(r"^(.*?)\s*\(([^)]*)\)?\s*$", rest)
        label = rest
        if pm and pm.group(2).strip():
            main, paren = pm.group(1).strip(), pm.group(2).strip()
            words = [w.strip(".,").lower() for w in re.split(r"[\s+]+", main) if w]
            if re.match(r"^\d", paren) or (words and all(w in _ENGLISH for w in words)):
                label = re.sub(r"^\d+\s+", "", paren)
            else:
                label = f"{main} ({paren})"
        label = re.sub(r"\bWC V\.?", "WC visiteurs", label).replace("+", " + ")
        label = " ".join(w if (w.isupper() and len(w) <= 3) else w.lower() for w in label.strip(" :").split())
        item = f"{n} {_pluriel(n, label)}".strip()
        if label and len(item) <= 42 and item not in out:        # les puces-phrases (« 2 chambres (12,67 m² …) avec une salle d'eau ») sont ignorées
            out.append(item)
    return out[:limit]


def levels_label(levels) -> str:
    return {1: "plain-pied", 2: "2 niveaux (R+1)"}.get(levels, f"{levels} niveaux" if levels else "")


def _plural(n, one: str, many: str) -> str:
    return one if n == 1 else many


# ---------------------------------------------------------------- lecture de la fiche publique du site

_DL = re.compile(r"<dt[^>]*>\s*([^<]+?)\s*</dt>\s*<dd[^>]*>\s*([^<]+?)\s*</dd>")
_THUMB = re.compile(r'aria-label="Voir l(?:\'|&#x27;)image \d+"[^>]*><img[^>]*?src="(/media/[^"]+)"')
_NUM = re.compile(r"\d+(?:[.,]\d+)?")


def _nums(s: str) -> List[float]:
    return [float(x.replace(",", ".")) for x in _NUM.findall(s or "")]


def _clean(x):
    return int(x) if isinstance(x, float) and x.is_integer() else x


def parse_levels(txt: str) -> Optional[int]:
    t = (txt or "").strip().lower()
    m = re.match(r"r\s*\+\s*(\d+)", t)
    if m:
        return int(m.group(1)) + 1
    if "plain" in t or t in ("rdc", "r+0"):
        return 1
    n = _nums(t)
    return int(n[0]) if n else None


def parse_gallery(html: str, code: str) -> List[str]:
    """Chemins des rendus publics (couverture en premier) : miniatures « Voir l'image N », sinon le dossier du plan."""
    found = _THUMB.findall(html)
    if not found:
        found = re.findall(r"(/media/public/%s/[A-Za-z0-9_\-.]+?\.(?:webp|jpe?g|png))" % re.escape(code.lower()), html)
    return list(dict.fromkeys(_html.unescape(p).split("?")[0] for p in found))      # sans « ?w=160 » : image complète


def parse_public_page(html: str, code: str) -> dict:
    """Champs publics d'une fiche https://www.wooplans.com/catalogue/<slug>. Vide si la page n'a pas la forme attendue."""
    rows = {k.strip().lower(): v.strip() for k, v in _DL.findall(html)}
    if "chambres" not in rows or "surface totale" not in rows:
        return {}
    d: dict = {"bedrooms": int(_nums(rows["chambres"])[0])}
    if "salles de bain" in rows:
        d["bathrooms"] = int(_nums(rows["salles de bain"])[0])
    if "niveaux" in rows:
        d["levels"] = parse_levels(rows["niveaux"])
    d["surface_total"] = _clean(_nums(rows["surface totale"])[0])
    bd = _nums(rows.get("dimensions du bâtiment", ""))
    d["building_width"], d["building_depth"] = (_clean(bd[0]), _clean(bd[1])) if len(bd) >= 2 else (None, None)
    td = _nums(rows.get("terrain nécessaire", ""))
    d["land_area"] = _clean(td[0]) if td else None
    d["land_width"], d["land_depth"] = (_clean(td[1]), _clean(td[2])) if len(td) >= 3 else (None, None)
    m = re.search(r'<meta name="description" content="([^"]*)"', html)
    if m:
        d["summary"] = _html.unescape(m.group(1)).strip()
    m = re.search(r"<h1[^>]*>([^<]+)", html)
    if m:
        d["name"] = _html.unescape(m.group(1)).strip()
    d["renders"] = parse_gallery(html, code)
    return d


def parse_sitemap(xml: str) -> List[dict]:
    """Modèles du catalogue listés dans le sitemap : [{code, slug, category}], triés par code."""
    out = []
    for loc in re.findall(r"<loc>([^<]+)</loc>", xml):
        m = re.search(r"/catalogue/((duplex|villa)-([a-z]\d-\d{3}))/?$", loc)
        if m:
            out.append({"code": m.group(3).upper(), "slug": m.group(1), "category": m.group(2)})
    return sorted(out, key=lambda x: x["code"])


# ---------------------------------------------------------------- données locales (instantanés du site)

def snap_path(code: str, data: Path = DATA) -> Path:
    return data / f"{code}.json"


def load_all(data: Path = DATA) -> Dict[str, dict]:
    out = {}
    for p in sorted(data.glob("*.json")):
        s = json.loads(p.read_text(encoding="utf-8"))
        out[s["code"]] = s
    return out


def save_snapshot(snap: dict, data: Path = DATA) -> Path:
    data.mkdir(parents=True, exist_ok=True)
    p = snap_path(snap["code"], data)
    p.write_text(json.dumps(snap, ensure_ascii=False, indent=1, sort_keys=True) + "\n", encoding="utf-8")
    return p


def apply_public(snap: dict, page: dict) -> dict:
    """Met à jour les champs publics d'un instantané (le site fait foi : un champ disparu du site est effacé)."""
    for k in PUBLIC_FIELDS:
        if k in page:
            snap[k] = page[k]
        elif k in DIM_FIELDS:
            snap[k] = None
    return snap


STD_LOTS = {
    10: ["Fondation", "Élévation RDC", "Dalle", "Élévation étage", "Charpente et toiture", "Crépissage et antivols",
         "Portes et fenêtres", "Plomberie et électricité", "Plafond et peinture", "Carrelage"],
    8: ["Fondation", "Élévations", "Charpente et toiture", "Crépissage et antivols", "Portes et fenêtres",
        "Plomberie et électricité", "Plafond et peinture", "Carrelage"],
}


def _lots(raw: list) -> List[dict]:
    """Devis par lot : objets {label, amount}, paires [libellé, montant], ou montants seuls (libellés standard 10 ou 8 lots)."""
    out = []
    for i, l in enumerate(raw):
        if isinstance(l, (int, float)):
            out.append({"label": STD_LOTS[len(raw)][i], "amount": int(l)})
        elif isinstance(l, (list, tuple)):
            out.append({"label": l[0], "amount": int(l[1])})
        else:
            out.append({"label": l["label"], "amount": int(l["amount"])})
    return out


def ingest_payload(payload: dict, snap: Optional[dict] = None) -> dict:
    """Champs Premium d'une réponse `get_plan` du connecteur, ou de sa forme compacte
    {code, description, total, lots, plans} (lots : montants seuls si les libellés sont les standards)."""
    snap = snap or {"code": payload["code"], "slug": payload.get("slug"), "category": payload.get("category")}
    prem = payload.get("premium") or {}
    if prem or any(k in payload for k in ("lots", "estimate_lots", "total", "estimate_total", "plans", "floor_plans")):   # sinon : mise à jour partielle (ex. originaux seuls)
        snap["estimate_lots"] = _lots(prem.get("estimate_lots", payload.get("estimate_lots", payload.get("lots"))) or [])
        snap["estimate_total"] = int(prem.get("estimate_total", payload.get("estimate_total", payload.get("total"))) or 0)
        plans = prem.get("floor_plans", payload.get("floor_plans", payload.get("plans"))) or []
        snap["floor_plans"] = [p if isinstance(p, str) else p["key"] for p in plans]
    if payload.get("originals") is not None:               # {nom du rendu public : clé R2 de l'original}
        snap["originals"] = dict(payload["originals"])
    if payload.get("description") is not None:
        snap["description"] = payload["description"]
    for k in ("name", "slug", "category", "summary", "bedrooms", "bathrooms", "levels", "surface_total"):
        if payload.get(k) is not None and k not in snap:
            snap[k] = payload[k]
    return snap


# ---------------------------------------------------------------- fichiers (plans, rendus) et complétude

def plan_files(code: str, plans: Path = PLANS) -> List[Path]:
    exts = {".png", ".jpg", ".jpeg", ".webp"}
    return sorted(p for p in plans.glob(f"{code}-*") if p.suffix.lower() in exts)


def cache_path(code: str, media_path: str, cache: Path = CACHE) -> Path:
    return cache / code / media_path.rsplit("/", 1)[-1]


def load_overrides(path: Path = OVERRIDES) -> dict:
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}


def orig_path(code: str, media_path: str, orig: Path = ORIG) -> Path:
    """Original sans filigrane (R2) d'un rendu public, s'il a été récupéré : orig/<code>/<nom du rendu public>.jpg."""
    return orig / code / (media_path.rsplit("/", 1)[-1].rsplit(".", 1)[0] + ".jpg")


def render_sources(snap: dict, overrides: Optional[dict] = None, cache: Path = CACHE, hires: Path = HIRES, orig: Path = ORIG) -> List[Path]:
    """Trois rendus pour la fiche, par ordre de préférence :
    1. `hires/<code>/<n>.*` (choix manuels) ; `cover_file` d'`overrides.json` pour la couverture ;
    2. les originaux R2 (orig/<code>/) : les trois premiers rendus du site (couverture d'abord) qui ont un original ;
       `render_picks` force d'autres positions du site ;
    3. à défaut, les rendus publics du site (960 px, filigranés)."""
    code = snap["code"]
    ov = (overrides or {}).get(code, {})
    renders = snap.get("renders") or []
    if ov.get("render_picks"):
        order, picks = renders, ov["render_picks"][:3]
    else:
        have = [r for r in renders if orig_path(code, r, orig).exists()][:3]
        order, picks = have + [r for r in renders if r not in have], [1, 2, 3]
    out: List[Path] = []
    for slot, pos in enumerate(picks, start=1):
        local = sorted((hires / code).glob(f"{slot}.*")) if (hires / code).is_dir() else []
        if local:
            out.append(local[0])
        elif slot == 1 and ov.get("cover_file"):
            out.append(ROOT / ov["cover_file"])
        elif 0 < pos <= len(order):
            r = order[pos - 1]
            op = orig_path(code, r, orig)
            out.append(op if op.exists() else cache_path(code, r, cache))
    return out


def missing_data(snap: dict, plans: List[Path]) -> List[str]:
    """Ce qui manque pour une fiche complète (vide = prête)."""
    miss = []
    if not snap.get("estimate_lots") or not snap.get("estimate_total"):
        miss.append("devis")
    if not plans:
        miss.append("plan de distribution")
    if not snap.get("renders"):
        miss.append("rendus")
    for k in ("bedrooms", "surface_total"):
        if not snap.get(k):
            miss.append(k)
    return miss


# ---------------------------------------------------------------- HTML

def css() -> str:
    return """
@font-face { font-family: 'Poppins'; src: url('../fonts/Poppins-Bold.ttf'); font-weight: 700; }
@page { size: 420mm 297mm; margin: 0; }
:root { --green:#0F5B59; --orange:#F08A2E; --dark:#1E2933; --light:#F5F7F9; --grey:#5B6670; }
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: #fff; color: var(--dark); font-family: 'Poppins', 'Helvetica Neue', Arial, sans-serif; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
a { color: inherit; text-decoration: none; }
.page { width: 420mm; height: 297mm; position: relative; overflow: hidden; break-after: page; page-break-after: always; }
.sheet { width: 420mm; height: 297mm; padding: 9mm 10mm 7mm; display: grid; grid-template-rows: 22mm minmax(0, 1fr) 8mm; row-gap: 4mm; overflow: hidden; }
header { display: flex; align-items: center; justify-content: space-between; background: var(--green); color: #fff; border-radius: 3mm; padding: 0 9mm; }
header .ref { font-size: 11pt; letter-spacing: .25em; text-transform: uppercase; opacity: .85; }
header h1 { font-size: 27pt; line-height: 1; font-weight: 700; }
header h1 span { color: var(--orange); }
header .tags { font-size: 10.5pt; text-align: right; line-height: 1.5; }
.body { display: grid; grid-template-columns: 118mm 140mm 132mm; grid-template-rows: minmax(0, 1fr); column-gap: 5mm; min-height: 0; }
h2 { font-size: 10.5pt; text-transform: uppercase; letter-spacing: .12em; color: var(--green); border-bottom: .6mm solid var(--orange); padding-bottom: 1mm; margin-bottom: 2mm; font-weight: 700; }
.col1 { display: flex; flex-direction: column; gap: 3.2mm; min-height: 0; overflow: hidden; }
.col3 { display: flex; flex-direction: column; gap: 3.2mm; min-height: 0; overflow: hidden; }
.desc p { font-size: 8.7pt; line-height: 1.5; color: var(--dark); }
.stats { display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 2.2mm; }
.stat { background: var(--light); border-left: 1.2mm solid var(--orange); padding: 2mm 2.4mm; border-radius: 1.5mm; }
.stat b { display: block; font-size: 17pt; color: var(--green); line-height: 1.05; }
.stat small { font-size: 7.6pt; color: var(--grey); line-height: 1.2; display: block; }
.comp { font-size: 8.2pt; line-height: 1.4; columns: 2; column-gap: 4mm; }
.comp.one { columns: 1; font-size: 8.6pt; line-height: 1.55; }
.comp li { list-style: none; padding-left: 3mm; position: relative; break-inside: avoid; }
.comp li::before { content: ''; position: absolute; left: 0; top: .55em; width: 1.4mm; height: 1.4mm; background: var(--orange); border-radius: 50%; }
.terrain { background: var(--green); color: #fff; border-radius: 2.5mm; padding: 2.4mm 4mm; }
.terrain h2 { color: #fff; }
.terrain .row { display: flex; justify-content: space-between; gap: 2mm; font-size: 8.4pt; white-space: nowrap; padding: 1mm 0; border-bottom: .2mm dashed rgba(255,255,255,.35); }
.terrain .row:last-child { border-bottom: none; }
table.devis { width: 100%; border-collapse: collapse; font-size: 7.9pt; }
table.devis td { padding: .6mm 1.5mm; border-bottom: .2mm solid #D9DEE3; }
table.devis td.n { color: var(--grey); width: 7mm; }
table.devis td.a { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
table.devis tr.tot td { background: var(--orange); color: #fff; font-size: 10.5pt; border: none; padding: 2mm 1.5mm; }
.col2 { display: grid; grid-template-rows: repeat(3, auto); gap: 3.2mm; align-content: start; }
.shot { position: relative; width: 140mm; height: 78.75mm; border-radius: 2mm; overflow: hidden; background: #E4E8EC; }
.shot img { width: 100%; height: 100%; object-fit: cover; display: block; }
.shot .cap { position: absolute; left: 0; bottom: 0; background: rgba(15,91,89,.88); color: #fff; font-size: 7.4pt; padding: 1mm 2.4mm; border-top-right-radius: 1.5mm; letter-spacing: .06em; text-transform: uppercase; }
.shot.cover .cap { background: var(--orange); }
.plan { border: .3mm solid #D9DEE3; border-radius: 2mm; padding: 2mm; background: #fff; }
.plan h4 { font-size: 8.6pt; color: var(--green); margin-bottom: 1.2mm; text-transform: uppercase; letter-spacing: .08em; }
.plan img { width: 100%; height: auto; object-fit: contain; display: block; }
.legend { font-size: 7.4pt; color: var(--grey); line-height: 1.4; }
footer { display: flex; justify-content: space-between; align-items: center; font-size: 8.4pt; color: var(--grey); border-top: .3mm solid #D9DEE3; padding-top: 1.5mm; }
footer b { color: var(--green); }
footer .pg { color: var(--dark); }
footer .pg a { color: var(--green); }
/* couverture, séparateurs, sommaire */
.titlepage { background: var(--green); color: #fff; padding: 22mm 24mm; display: flex; flex-direction: column; justify-content: space-between; }
.titlepage .logo { height: 34mm; align-self: flex-start; }
.titlepage h1 { font-size: 62pt; line-height: 1.02; }
.titlepage h1 span { color: var(--orange); }
.titlepage .sub { font-size: 20pt; margin-top: 8mm; opacity: .92; }
.titlepage .meta { font-size: 13pt; line-height: 1.7; border-top: .6mm solid var(--orange); padding-top: 6mm; }
.divider { background: var(--green); color: #fff; padding: 22mm 24mm; display: flex; flex-direction: column; justify-content: center; }
.divider.v { background: var(--orange); }
.divider h1 { font-size: 96pt; line-height: 1; }
.divider p { font-size: 20pt; margin-top: 8mm; }
.divider small { display: block; font-size: 12pt; margin-top: 4mm; opacity: .85; }
.sommaire { padding: 12mm 10mm 7mm; display: flex; flex-direction: column; }
.sommaire h1 { font-size: 30pt; color: var(--green); border-bottom: .8mm solid var(--orange); padding-bottom: 3mm; margin-bottom: 6mm; }
.cols { flex: 1; display: grid; grid-template-columns: repeat(4, 1fr); column-gap: 8mm; min-height: 0; align-content: start; }
.cols h2 { margin-top: 0; }
.cols .e { display: flex; align-items: baseline; font-size: 7.6pt; line-height: 1; padding: 1.35mm 0; }
.cols .e .c { width: 14mm; color: var(--green); }
.cols .e .d { color: var(--grey); }
.cols .e .dots { flex: 1; border-bottom: .3mm dotted #9AA5AE; margin: 0 1.5mm; }
.cols .e .n { width: 7mm; text-align: right; }
.sommaire footer { margin-top: 4mm; }
"""


def _rel(p: Path, out: Path = OUT) -> str:
    return os.path.relpath(p, out).replace(os.sep, "/")


PLAN_MAX_MM = {1: 120, 2: 98, 3: 64, 4: 46}


def _plan_names(n: int, levels) -> List[str]:
    """RDC / étage seulement dans le cas sûr (2 plans, 2 niveaux) ; sinon libellés neutres : le site ne dit pas ce que contient
    chaque fichier (ex. un 3e fichier qui est un tableau de surfaces)."""
    if n == 2 and levels == 2:
        return ["Plan du rez-de-chaussée", "Plan de l'étage"]
    return ["Plan de distribution"] if n == 1 else [f"Plan de distribution {i + 1}/{n}" for i in range(n)]


def model_data(snap: dict, overrides: Optional[dict] = None, plans: Optional[List[Path]] = None, renders: Optional[List[Path]] = None) -> dict:
    plans = plan_files(snap["code"]) if plans is None else plans
    skip = set(((overrides or {}).get(snap["code"]) or {}).get("skip_plans") or [])       # fichiers qui ne sont pas des plans (1 = premier)
    plans = [p for i, p in enumerate(plans, 1) if i not in skip]
    return {"snap": snap, "plans": plans,
            "renders": render_sources(snap, overrides) if renders is None else renders,
            "intro": intro_paragraph(snap), "features": parse_features(snap.get("description") or "")}


def model_problems(m: dict) -> List[str]:
    """Écarts à signaler (non bloquants) : devis incohérent, texte refusé par check_copy."""
    from wooplans.guardrails import check_copy
    s = m["snap"]
    lots = s.get("estimate_lots") or []
    out = []
    if lots and sum(l["amount"] for l in lots) != s.get("estimate_total"):
        out.append(f"devis : somme des lots {money(sum(l['amount'] for l in lots))} ≠ total {money(s.get('estimate_total') or 0)}")
    allowed = [l["amount"] for l in lots] + [s.get("estimate_total") or 0]
    out += [f"texte : {p}" for p in check_copy(" ".join([m["intro"]] + m["features"]), allowed)]
    return out


def model_page(m: dict, number: int, total: int, section: str) -> str:
    s = m["snap"]
    code, kind = s["code"], dict(CATEGORIES).get(s.get("category"), "Modèle")
    b, ba, lv, surf = s.get("bedrooms"), s.get("bathrooms"), s.get("levels"), s.get("surface_total")
    bw, bd, lw, ld, la = (s.get(k) for k in ("building_width", "building_depth", "land_width", "land_depth", "land_area"))
    tags1 = " · ".join(x for x in (f"{b} {_plural(b, 'chambre', 'chambres')}" if b else "",
                                   f"{ba} {_plural(ba, 'salle de bain', 'salles de bain')}" if ba else "", levels_label(lv)) if x)
    tags2 = " · ".join(x for x in (f"{surf} m² de surface totale" if surf else "",
                                   f"emprise {fr_num(bw)} × {fr_num(bd)} m" if bw and bd else "") if x)
    plans = m["plans"]
    one_plan = len(plans) == 1
    feats = m["features"]
    feat_html = "".join(f"<li>{esc(f)}</li>" for f in feats)
    rows = []
    if bw and bd:
        rows.append(("Emprise au sol du bâtiment", f"{fr_num(bw)} × {fr_num(bd)} m"))
    if lw and ld:
        rows.append(("Terrain nécessaire", f"{fr_num(lw)} × {fr_num(ld)} m"))
    if la:
        rows.append(("Surface de terrain", f"{fr_num(la)} m²"))
    terrain = ('<section class="terrain"><h2>Terrain et emprise</h2>' + "".join(
        f'<div class="row"><span>{esc(a)}</span><b>{esc(v)}</b></div>' for a, v in rows) + "</section>") if rows else ""
    lots = s.get("estimate_lots") or []
    tot = s.get("estimate_total") or sum(l["amount"] for l in lots)
    devis = ('<section><h2>Devis estimatif · clé en main (FCFA)</h2><table class="devis">' + "".join(
        f'<tr><td class="n">{i}</td><td>{esc(l["label"])}</td><td class="a">{money(l["amount"])}</td></tr>' for i, l in enumerate(lots, 1))
        + f'<tr class="tot"><td></td><td>Total clé en main</td><td class="a">{money(tot)}</td></tr></table></section>') if lots else ""
    stats = "".join(f'<div class="stat"><b>{esc(v)}</b><small>{esc(t)}</small></div>' for v, t in (
        (b, _plural(b, "chambre", "chambres")), (ba, _plural(ba, "salle de bain", "salles de bain")), (surf, "m² de surface totale")) if v)
    names = _plan_names(len(plans), lv)
    ph = PLAN_MAX_MM.get(len(plans), 40)
    plan_html = "".join(
        f'<div class="plan"><h4>{esc(n)}</h4><img src="{_rel(p)}" style="max-height:{ph}mm" alt="{esc(n)}"></div>' for n, p in zip(names, plans))
    r = m["renders"]
    shots = "".join(f'<div class="shot{" cover" if i == 0 else ""}"><img src="{_rel(p)}" alt="{esc(CAPTIONS[i])}"><span class="cap">{esc(CAPTIONS[i])}</span></div>'
                    for i, p in enumerate(r[:3]))
    comp_col1 = f'<section><h2>Caractéristiques</h2><ul class="comp">{feat_html}</ul></section>' if feats and not one_plan else ""
    comp_col3 = f'<section><h2>Composition</h2><ul class="comp one">{feat_html}</ul></section>' if feats and one_plan else ""
    return f"""
<section class="page model" id="p-{esc(code)}" data-code="{esc(code)}"><div class="sheet">
<header><div><div class="ref">Présentation de plan · WooPlans</div><h1>{esc(kind)} <span>{esc(code)}</span></h1></div>
<div class="tags"><b>{esc(tags1)}</b><br>{esc(tags2)}</div></header>
<div class="body">
<div class="col1"><section class="desc"><h2>Le modèle</h2><p>{esc(m['intro'])}</p></section>
<section><div class="stats">{stats}</div></section>{comp_col1}{terrain}{devis}</div>
<div class="col2">{shots}</div>
<div class="col3">{plan_html}{comp_col3}<p class="legend">Cotes en mètres. Devis : coûts indicatifs, ils dépendent du type de sol, des techniciens et des matériaux. Données : fiche du modèle sur wooplans.com.</p></div>
</div>
<footer><span><b>WooPlans</b> · Catalogue Premium · wooplans.com/catalogue-premium</span>
<span class="pg"><a href="#sommaire">{esc(section)} · {esc(code)} · page {number} / {total}</a></span>
<span>Document de présentation · Ne pas utiliser pour la construction</span></footer>
</div></section>"""


# ---------------------------------------------------------------- structure du document (pagination, sommaire)

def group_models(models: List[dict], part: str = "all") -> List[Tuple[str, str, List[dict]]]:
    groups = []
    for key, label in CATEGORIES:
        if part in ("all", key):
            ms = sorted((m for m in models if m["snap"].get("category") == key), key=lambda m: m["snap"]["code"])
            if ms:
                groups.append((key, label, ms))
    return groups


def layout(groups: List[Tuple[str, str, List[dict]]]) -> dict:
    """Numéros de page : 1 couverture, puis sommaire (1+ pages), puis pour chaque partie : séparateur + une page par modèle."""
    ncols = sum(math.ceil(len(ms) / ROWS_PER_COL) for _, _, ms in groups)
    s_pages = max(1, math.ceil(ncols / COLS_PER_PAGE))
    page = 2 + s_pages
    pages, divs = {}, {}
    for key, _, ms in groups:
        divs[key] = page
        page += 1
        for m in ms:
            pages[m["snap"]["code"]] = page
            page += 1
    return {"sommaire_pages": s_pages, "model_page": pages, "divider_page": divs, "total": page - 1}


def cover_page(groups, total_models: int, today: date, logo: Optional[Path]) -> str:
    counts = " · ".join(f"{len(ms)} {'duplex' if key == 'duplex' else _plural(len(ms), 'villa', 'villas')}" for key, _, ms in groups)
    img = f'<img class="logo" src="{_rel(logo)}" alt="WooPlans">' if logo and logo.exists() else '<div></div>'
    return f"""
<section class="page titlepage" id="couverture">{img}
<div><h1>Catalogue <span>Premium</span></h1><div class="sub">Fiches de présentation A3 · {total_models} modèles</div></div>
<div class="meta">{esc(counts)}<br>Édition du {esc(fr_date(today))}<br>wooplans.com/catalogue-premium</div></section>"""


def divider_page(key: str, label: str, ms: List[dict], first: int, last: int) -> str:
    codes = f"{ms[0]['snap']['code']} → {ms[-1]['snap']['code']}"
    plural = "Duplex" if key == "duplex" else "Villas"
    return f"""
<section class="page divider {'v' if key == 'villa' else ''}" id="partie-{key}"><h1>{plural}</h1>
<p>{len(ms)} {_plural(len(ms), 'modèle', 'modèles')} · {'page ' + str(first) if first == last else f'pages {first} à {last}'}</p><small>{esc(codes)}</small></section>"""


def sommaire_pages(groups, lay: dict, today: date) -> str:
    cols: List[Tuple[str, bool, List[dict]]] = []
    for _, label, ms in groups:
        for i in range(0, len(ms), ROWS_PER_COL):
            cols.append((label if label == "Duplex" else "Villas", i > 0, ms[i:i + ROWS_PER_COL]))
    html_pages = []
    for pi in range(lay["sommaire_pages"]):
        chunk = cols[pi * COLS_PER_PAGE:(pi + 1) * COLS_PER_PAGE]
        col_html = ""
        for title, cont, ms in chunk:
            ents = ""
            for m in ms:
                s = m["snap"]
                code = s["code"]
                desc = " · ".join(x for x in (f"{s['bedrooms']} ch" if s.get("bedrooms") else "", f"{s['surface_total']} m²" if s.get("surface_total") else "",
                                              f"terrain {s['land_area']} m²" if s.get("land_area") else "") if x)
                ents += (f'<a class="e" href="#p-{esc(code)}"><span class="c">{esc(code)}</span><span class="d">{esc(desc)}</span>'
                         f'<span class="dots"></span><span class="n">{lay["model_page"][code]}</span></a>')
            col_html += f'<div><h2>{esc(title)}{" (suite)" if cont else ""}</h2>{ents}</div>'
        total = lay["total"]
        html_pages.append(f"""
<section class="page sommaire" {'id="sommaire"' if pi == 0 else ''}><h1>Sommaire</h1><div class="cols">{col_html}</div>
<footer><span><b>WooPlans</b> · Catalogue Premium · wooplans.com/catalogue-premium</span><span class="pg">Sommaire · page {2 + pi} / {total}</span><span>Édition du {esc(fr_date(today))}</span></footer></section>""")
    return "".join(html_pages)


def build_document(models: List[dict], part: str = "all", today: Optional[date] = None, logo: Optional[Path] = None) -> Tuple[str, dict]:
    """HTML complet (couverture, sommaire, séparateurs, fiches) et structure de pagination."""
    today = today or date.today()
    groups = group_models(models, part)
    lay = layout(groups)
    body = [cover_page(groups, sum(len(ms) for _, _, ms in groups), today, logo), sommaire_pages(groups, lay, today)]
    for key, label, ms in groups:
        first = lay["model_page"][ms[0]["snap"]["code"]]
        body.append(divider_page(key, label, ms, first, lay["model_page"][ms[-1]["snap"]["code"]]))
        for m in ms:
            body.append(model_page(m, lay["model_page"][m["snap"]["code"]], lay["total"], "Duplex" if key == "duplex" else "Villa"))
    title = {"all": "Catalogue Premium A3", "duplex": "Catalogue Premium A3 · Duplex", "villa": "Catalogue Premium A3 · Villas"}[part]
    doc = f'<!doctype html><html lang="fr"><head><meta charset="utf-8"><title>{esc(title)}</title><style>{css()}</style></head><body>{"".join(body)}</body></html>'
    return doc, lay
