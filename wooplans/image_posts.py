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
from wooplans.settings import OFFER_PRICE_FCFA, OFFER_PROMISE, ROOT
from wooplans.utm import build_link

PLANS = ROOT / "data" / "plans.json"
FMT = "I"                                     # format « image » dans le registre anti-doublon
TZ = "Africa/Douala"
DEFAULT_SLOTS = ["07:30", "12:30", "17:30"]   # laisse le soir (19 h et après) aux vidéos
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

def _tags(p: dict) -> str:
    return f"#plandemaison #{p['category']} #maison #construction #architecture #Afrique"


def _link(p: dict) -> str:
    return build_link("facebook", FMT, p["code"])


def _ctx(p: dict) -> dict:
    return {
        "name": p["name"], "type": p["category"], "ch": p["bedrooms"], "surf": p["surface"],
        "land": p.get("land_area"), "est": fcfa(p["estimate_total"]), "link": _link(p), "tags": _tags(p),
        "promise": OFFER_PROMISE, "price": fcfa(OFFER_PRICE_FCFA),
    }


TEMPLATES = [
    ("fiche", False,
     "🏡 {name} · {ch} chambres · {surf} m²\nEstimation indicative : {est} FCFA.\n\n"
     "📲 Plan complet + devis détaillé dans le Catalogue Premium ({promise}), prix actuel : {price} FCFA.\n👉 {link}\n\n{tags}"),
    ("question", False,
     "Ce {type} de {ch} chambres, vous le construiriez ? 😍\nDites-nous en commentaire ce que vous modifieriez.\n\n"
     "{name} · {surf} m² · estimation indicative : {est} FCFA\n\n👉 Tous nos plans avec leurs vrais devis : {link}\n\n{tags}"),
    ("terrain", True,
     "Quel plan pour un terrain de {land} m² ? 📐\n{name} : {ch} chambres, {surf} m², terrain prévu : {land} m².\n"
     "Estimation indicative : {est} FCFA.\n\n👉 Le plan et son devis détaillé : {link}\n\n{tags}"),
    ("budget", False,
     "Un budget de construction autour de {est} FCFA ? 💰\n{name} : {ch} chambres, {surf} m² (estimation indicative).\n\n"
     "Le devis détaillé est dans le Catalogue Premium, prix actuel : {price} FCFA.\n👉 {link}\n\n{tags}"),
    ("enregistrer", False,
     "📌 Enregistrez ce plan pour votre futur projet !\n{name} · {ch} chambres · {surf} m²\n\n"
     "{promise} : {link}\n\n{tags}"),
    ("partage", False,
     "Quelqu'un prépare sa construction autour de vous ? Partagez-lui ce plan 👇\n"
     "{name} · {ch} chambres · {surf} m² · estimation indicative : {est} FCFA\n\n"
     "👉 {promise} : {link}\n\n{tags}"),
]


def caption(p: dict, start_index: int = 0) -> Tuple[str, str]:
    """(nom du modèle de légende, texte). Passe par check_copy ; lève ValueError si un garde-fou refuse."""
    ctx = _ctx(p)
    for i in range(len(TEMPLATES)):
        name, needs_land, text = TEMPLATES[(start_index + i) % len(TEMPLATES)]
        if needs_land and not ctx["land"]:
            continue
        out = text.format(**ctx)
        problems = check_copy(out, [p["estimate_total"]])
        if problems:
            raise ValueError(f"{p['code']} : {problems}")
        return name, out
    raise ValueError(f"{p['code']} : aucune légende applicable")


# ---------- lot de la semaine ----------

def build_batch(plans: List[dict], start: date, days: int, images_for: Callable[[str], List[str]],
                usage: Optional[Dict[str, int]] = None, used_imgs: Optional[Dict[str, Set[str]]] = None,
                slots: Optional[List[str]] = None, seed: int = 0) -> List[dict]:
    """Un post par créneau. Les plans les moins publiés passent d'abord ; on alterne villa/duplex ;
    jamais deux fois le même plan le même jour ; un rendu déjà publié n'est repris qu'après avoir fait le tour du plan."""
    slots = slots or DEFAULT_SLOTS
    rng = random.Random(seed)
    count = dict(usage or {})
    used = {k: set(v) for k, v in (used_imgs or {}).items()}
    cache: Dict[str, List[str]] = {}

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
            order = sorted(plans, key=lambda p: (count.get(p["code"], 0), rng.random()))
            choice = None
            for prefer_other in (True, False):
                for p in order:
                    if p["code"] in day_codes or (prefer_other and p["category"] == prev_cat):
                        continue
                    if imgs(p["code"]):
                        choice = p
                        break
                if choice:
                    break
            if not choice:
                continue
            code = choice["code"]
            kind = PATTERNS[si % len(PATTERNS)]
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
            tname, text = caption(choice, start_index=n + seed)
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
