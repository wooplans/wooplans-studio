"""Posts images Facebook : choix du plan et des rendus, légendes variées, créneaux de la semaine.

Logique pure (aucun réseau) : les URL des rendus sont fournies par l'appelant (`images_for`).
Règles du projet respectées ici : prix/surfaces uniquement ceux de data/plans.json, `check_copy` sur chaque légende,
lien du catalogue premium avec UTM, jamais de formule d'urgence.
"""
import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Dict, List, Optional, Set, Tuple

from wooplans.guardrails import check_copy
from wooplans.registry import REGISTRY, _load
from wooplans.settings import ROOT
from wooplans.utm import free_link

PLANS = ROOT / "data" / "plans.json"
FMT = "I"                                     # format « image » dans le registre anti-doublon
TZ = "Africa/Douala"
DEFAULT_SLOTS = ["07:30", "12:30", "19:00"]   # décision de Tao du 20 oct. : 7 h 30, 12 h 30, 19 h
PATTERNS = ["single", "album", "single"]      # par créneau : 1 rendu, 4 rendus, 1 rendu
ALBUM_SIZE = 4
DAYS_FR = ["lun.", "mar.", "mer.", "jeu.", "ven.", "sam.", "dim."]


def load_plans(path: Path = PLANS) -> List[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def fcfa(n: int) -> str:
    return f"{n:,}".replace(",", " ")


def base(url: str) -> str:
    return url.rsplit("/", 1)[-1]


def usage_from_registry(path: Optional[Path] = None) -> Tuple[Dict[str, int], Dict[str, Set[str]]]:
    """Posts images déjà programmés : nombre par plan, et rendus déjà utilisés par plan."""
    count: Dict[str, int] = {}
    imgs: Dict[str, Set[str]] = {}
    for e in _load(path or REGISTRY).values():
        if e.get("format") != FMT or e.get("etat") != "programme":
            continue
        count[e["plan"]] = count.get(e["plan"], 0) + 1
        imgs.setdefault(e["plan"], set()).update(e.get("images", []))
    return count, imgs


# ---------- légendes ----------
# Format imposé par Tao (29 oct.) : accroche, fiche du plan (référence, chambres, niveaux, surface, terrain, budget en fourchette),
# invitation à commenter / enregistrer / partager, puis CTA vers le catalogue GRATUIT (lien court + utm_source seulement).
# Aucun prix du Catalogue Premium dans ces publications.

def _tags(p: dict) -> str:
    return f"#plandemaison #{p['category']} #maison #construction #architecture #Afrique"


def budget_range(p: dict) -> Tuple[int, int]:
    """Fourchette de budget affichée sur le catalogue : estimation du devis ± 10 %, arrondie à 100 000 FCFA."""
    est = p["estimate_total"]
    return int(est * 0.9 / 100_000 + 0.5) * 100_000, int(est * 1.1 / 100_000 + 0.5) * 100_000


def _ctx(p: dict) -> dict:
    villa = p["category"] == "villa"
    low, high = budget_range(p)
    return {
        "name": p["name"], "type": p["category"], "This": "Cette villa" if villa else "Ce duplex", "un": "une villa" if villa else "un duplex",
        "ch": p["bedrooms"], "niv": "de plain-pied" if p["levels"] == 1 else f"{p['levels']} niveaux", "surf": p["surface"],
        "land": p.get("land_area"), "low": fcfa(low), "high": fcfa(high), "link": free_link("facebook"), "tags": _tags(p),
    }


HOOKS = [
    ("coup-de-coeur", "😍 {This} de {ch} chambres : coup de cœur ou pas ?"),
    ("tout-pour-plaire", "✨ {This} de {ch} chambres a tout pour plaire."),
    ("projet", "🏗️ Vous préparez votre construction ? Découvrez {un} de {ch} chambres."),
    ("future-maison", "🏡 Et si c'était votre future maison ?"),
]
ENGAGE = [
    "💬 Dites-nous en commentaire ce que vous en pensez.",
    "📌 Enregistrez ce post pour votre futur projet.",
    "🔁 Partagez-le à quelqu'un qui prépare sa construction.",
]
TEMPLATES = HOOKS                                 # un modèle de légende par accroche


def caption(p: dict, start_index: int = 0, kind: str = "single") -> Tuple[str, str]:
    """(nom de l'accroche, texte). Passe par check_copy ; lève ValueError si un garde-fou refuse."""
    ctx = _ctx(p)
    name, hook = HOOKS[start_index % len(HOOKS)]
    lines = [hook.format(**ctx), "",
             f"🏠 {ctx['name']} · {ctx['ch']} chambres · {ctx['niv']}",
             f"📐 Surface : {ctx['surf']} m²"]
    if ctx["land"]:
        lines.append(f"🌿 Terrain prévu : {ctx['land']} m²")
    lines += [f"💰 Budget de construction estimé : {ctx['low']} – {ctx['high']} FCFA", ""]
    if kind == "album":
        lines.append("➡️ Faites défiler pour voir toutes les vues.")
    lines += [ENGAGE[start_index % len(ENGAGE)], "",
              "👉 Voir ce plan et tous les autres dans notre catalogue gratuit :", ctx["link"], "", ctx["tags"]]
    out = "\n".join(lines)
    low, high = budget_range(p)
    problems = check_copy(out, [p["estimate_total"], low, high])
    if problems:
        raise ValueError(f"{p['code']} : {problems}")
    return name, out


# ---------- lot de la semaine ----------

def build_batch(plans: List[dict], start: date, days: int, images_for: Callable[[str], List[str]],
                usage: Optional[Dict[str, int]] = None, used_imgs: Optional[Dict[str, Set[str]]] = None,
                slots: Optional[List[str]] = None, seed: int = 0,
                cats: Optional[List[str]] = None, patterns: Optional[List[str]] = None) -> List[dict]:
    """Un post par créneau. Les plans les moins publiés passent d'abord ; on alterne villa/duplex ;
    jamais deux fois le même plan le même jour ; un rendu déjà publié n'est repris qu'après avoir fait le tour du plan.
    `cats` impose la catégorie de chaque créneau (ex. 2 duplex + 2 villas par jour) et `patterns` le type de post
    (single / album) ; avec `cats`, un créneau « album » exige au moins 2 images et chaque créneau prend de préférence
    le plan dont le nombre d'images correspond (1 pour single, ALBUM_SIZE pour album) ; aucun plan n'est repris
    tant qu'il en reste d'inédits dans le lot."""
    slots = slots or DEFAULT_SLOTS
    patterns = patterns or PATTERNS
    rng = random.Random(seed)
    count = dict(usage or {})
    used = {k: set(v) for k, v in (used_imgs or {}).items()}
    cache: Dict[str, List[str]] = {}
    here: Dict[str, int] = {}                     # posts déjà placés dans CE lot (avec `cats`, un plan inédit passe avant un plan déjà vu)

    def imgs(code: str) -> List[str]:
        if code not in cache:
            cache[code] = list(dict.fromkeys(images_for(code)))
        return cache[code]

    posts: List[dict] = []
    prev_cat = None
    n = 0
    for d in range(days):
        day = start + timedelta(days=d)
        day_codes: Set[str] = set()
        for si, hhmm in enumerate(slots):
            kind = patterns[si % len(patterns)]
            cat = cats[si % len(cats)] if cats else None
            want = ALBUM_SIZE if kind == "album" else 1
            pool = [p for p in plans if cat is None or p["category"] == cat]
            if cat:
                order = sorted(pool, key=lambda p: (here.get(p["code"], 0), count.get(p["code"], 0),
                                                    abs(len(imgs(p["code"])) - want), rng.random()))
            else:
                order = sorted(pool, key=lambda p: (count.get(p["code"], 0), rng.random()))
            choice = None
            for prefer_other in (True, False):
                for p in order:
                    if p["code"] in day_codes or (prefer_other and not cat and p["category"] == prev_cat):
                        continue
                    if len(imgs(p["code"])) >= (2 if cat and kind == "album" else 1):
                        choice = p
                        break
                if choice:
                    break
            if not choice:
                continue
            code = choice["code"]
            urls = imgs(code)
            fresh = [u for u in urls if base(u) not in used.get(code, set())]
            if len(fresh) < (2 if kind == "album" else 1):
                used[code] = set()
                fresh = list(urls)
            if kind == "album" and len(fresh) >= 2:
                sel = fresh[:ALBUM_SIZE]
            else:
                kind, sel = "single", fresh[:1]
            used.setdefault(code, set()).update(base(u) for u in sel)
            count[code] = count.get(code, 0) + 1
            here[code] = here.get(code, 0) + 1
            tname, text = caption(choice, start_index=n + seed, kind=kind)
            posts.append({
                "id": f"{day.isoformat()}-{hhmm.replace(':', '')}", "when": f"{day.isoformat()}T{hhmm}:00",
                "timezone": TZ, "code": code, "name": choice["name"], "kind": kind, "images": sel,
                "template": tname, "caption": text, "skip": False,
            })
            day_codes.add(code)
            prev_cat = choice["category"]
            n += 1
    return posts


def day_label(iso: str) -> str:
    d = date.fromisoformat(iso[:10])
    return f"{DAYS_FR[d.weekday()]} {d.day:02d}/{d.month:02d} · {iso[11:16]}"
