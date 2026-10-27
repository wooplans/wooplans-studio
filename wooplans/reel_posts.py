"""Légendes des reels « rendus 3D en vidéo » : Facebook, YouTube Shorts, TikTok. Chiffres uniquement ceux de data/plans.json ;
tout texte passe par check_copy ; lien du catalogue avec UTM propre à chaque plateforme (format « R »)."""
from typing import Dict

from wooplans.guardrails import check_copy
from wooplans.reel3d import fcfa
from wooplans.settings import OFFER_PRICE_FCFA
from wooplans.utm import build_link

TAGS = {"facebook": "#plandemaison #maison #construction #Cameroun #Afrique",
        "youtube": "#plandemaison #maison #construction #shorts",
        "tiktok": "#plandemaison #construction #maison #Afrique #WooPlans"}


def _kind(plan: dict) -> str:
    return "villa" if plan["category"].lower().startswith("villa") else "duplex"


def facts(plan: dict) -> str:
    lv = "de plain-pied" if plan["levels"] == 1 else f"{plan['levels']} niveaux"
    s = f"{plan['bedrooms']} chambres · {plan['surface']} m² · {lv}"
    if plan.get("land_area"):
        s += f" · terrain prévu {plan['land_area']} m²"
    return s


def captions(plan: dict) -> Dict[str, dict]:
    k, code = _kind(plan), plan["code"]
    ce = "cette villa" if k == "villa" else "ce duplex"
    est = fcfa(plan["estimate_total"])
    out = {}
    for plat in ("facebook", "youtube", "tiktok"):
        link = build_link(plat, "R", code)
        body = (f"Combien coûte {ce} de {plan['bedrooms']} chambres ? 🏠\n\n{plan['name']} : {facts(plan)}.\n"
                f"Estimation indicative du budget pour construire : {est} FCFA.\n\n"
                f"📘 Plan complet + devis détaillé dans le Catalogue Premium, prix actuel : {fcfa(OFFER_PRICE_FCFA)} FCFA\n"
                f"👉 {link}\n\n{TAGS[plat]}")
        out[plat] = {"caption": body}
    out["youtube"] = {"title": f"{plan['name']} : {plan['bedrooms']} chambres, {plan['surface']} m² #shorts",
                      "description": out["youtube"]["caption"]}
    return out


def problems(plan: dict, caps: Dict[str, dict]) -> list:
    texts = [c.get("caption", "") for c in caps.values()] + [caps["youtube"]["title"]]
    return [p for t in texts for p in check_copy(t, [plan["estimate_total"]])] + \
           (["ancien lien cpbook"] if any("cpbook" in t for t in texts) else [])
