"""Shorts « rendus 3D » : infos d'un modèle et sélection de modèles à partir d'une demande libre.

Sélection (`resolve`) : mots séparés par des espaces ou des virgules, sans tenir compte des majuscules :
  « D4-004 V3-022 »  codes précis
  « villa », « duplex »  toute une catégorie (pluriel accepté)
  « V4 », « D5 »  famille de codes (D4 = tous les D4-xxx)
  « tous »  tout le catalogue publié
  « nouveaux »  (en plus) : seulement les modèles qui n'ont encore aucun short
Modèles : catalogue publié du site (list_plans) si le jeton est disponible, sinon data/plans.json.
"""
import json
import re
from pathlib import Path
from typing import List, Optional

from wooplans.settings import ROOT

JOBS = ROOT / "shorts" / "jobs"
CODE = re.compile(r"^[A-Z]\d+-\d+$")


def local_plans() -> List[dict]:
    return json.loads((ROOT / "data" / "plans.json").read_text(encoding="utf-8"))


def catalogue() -> List[dict]:
    """Modèles publiés au format de data/plans.json (code, category, bedrooms, surface, land_area)."""
    try:
        from wooplans import site_api
        return [{"code": p["code"], "category": p["category"], "bedrooms": p["bedrooms"], "levels": p.get("levels"),
                 "surface": p.get("surface_total"), "land_area": p.get("land_area")} for p in site_api.published_plans()]
    except Exception:
        return local_plans()


def plan_info(code: str, plans: Optional[List[dict]] = None) -> dict:
    """Chiffres d'un modèle : data/plans.json (PDF plans + devis) en priorité, sinon la fiche publiée du site."""
    p = next((p for p in local_plans() if p["code"] == code), None)
    if p:
        return p
    p = next((p for p in (plans if plans is not None else catalogue()) if p["code"] == code), None)
    if not p:
        raise KeyError(f"modèle inconnu : {code}")
    return p


def texts(p: dict):
    """Titre et ligne de chiffres affichés (aucun prix)."""
    kind = "Duplex" if p["category"] == "duplex" else "Villa"
    title = f"{kind} {p['bedrooms']} chambres"
    facts = (f"{p['surface']} m²" if p.get("surface") else "") + (f" · terrain {p['land_area']} m²" if p.get("land_area") else "")
    return title, facts.strip(" ·")


def has_short(code: str) -> bool:
    return any(JOBS.glob(f"{code}-S*/short.json"))


def resolve(selection: str, plans: Optional[List[dict]] = None) -> List[str]:
    plans = plans if plans is not None else catalogue()
    words = [w for w in re.split(r"[\s,;]+", selection.strip()) if w]
    only_new = any(w.lower() in ("nouveaux", "nouveau", "new") for w in words)
    codes, unknown = [], []
    for w in words:
        lw, uw = w.lower(), w.upper()
        if lw in ("nouveaux", "nouveau", "new"):
            continue
        if lw in ("tous", "tout", "all"):
            found = [p["code"] for p in plans]
        elif lw.rstrip("s") in ("villa", "duplex", "duplexe"):
            cat = "villa" if lw.startswith("villa") else "duplex"
            found = [p["code"] for p in plans if p["category"] == cat]
        elif CODE.match(uw):
            found = [uw] if any(p["code"] == uw for p in plans) else []
        elif re.match(r"^[VD]\d+$", uw):                    # famille de codes : D4 = D4-001, D4-002...
            found = [p["code"] for p in plans if p["code"].startswith(uw + "-")]
        else:
            found = []
        if not found:
            unknown.append(w)
        codes += [c for c in found if c not in codes]
    if unknown:
        raise ValueError(f"sélection non reconnue ou vide : {', '.join(unknown)}")
    return [c for c in codes if not (only_new and has_short(c))]
