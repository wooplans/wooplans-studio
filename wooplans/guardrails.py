"""Garde-fous de contenu, appliqués à toute voix off, légende ou texte à l'écran avant envoi.

Règles du projet : jamais « l'offre expire dans X heures » (le minuteur de la page se réinitialise) ;
aucun prix qui ne vienne pas de la source de vérité (PDF plans + devis, via data/plans.json) ou du prix actuel du catalogue.
"""
import re
from typing import Iterable, List

from wooplans.settings import OFFER_PRICE_FCFA

EXPIRE = re.compile(
    r"(offre\s+(?:\w+\s+){0,2}(?:expire|se\s+termine|prend\s+fin)|expire\s+dans|plus\s+que\s+\d+\s*(?:h|heures?|minutes?)"
    r"|compte\s+à\s+rebours|minuteur|dernières?\s+heures)", re.I)
AMOUNT = re.compile(r"(\d{1,3}(?:[   .]\d{3})+|\d+)\s*(?:fcfa|f\s?cfa|xaf|cfa|francs?)", re.I)


def amounts(text: str) -> List[int]:
    out = []
    for m in AMOUNT.finditer(text):
        out.append(int(re.sub(r"[^\d]", "", m.group(1))))
    return out


def check_copy(text: str, allowed_amounts: Iterable[int] = ()) -> List[str]:
    """Liste de problèmes (vide = OK)."""
    problems = []
    if EXPIRE.search(text):
        problems.append("urgence interdite : dire « prix actuel : 29 000 FCFA », jamais une expiration")
    ok = {OFFER_PRICE_FCFA, *allowed_amounts}
    for a in amounts(text):
        if a not in ok:
            problems.append(f"montant non sourcé : {a:,} FCFA".replace(",", " "))
    return problems
