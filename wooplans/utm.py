"""Liens de suivi : un lien par plateforme et par vidéo, lisible dans Chariow (sources de trafic)."""
from urllib.parse import urlencode

from wooplans.settings import FREE_CATALOGUE_URL, OFFER_URL

PLATFORMS = ("facebook", "tiktok", "youtube")
FORMATS = {"A": "visite", "B": "cout", "I": "image", "R": "reel3d"}
MEDIUMS = {"I": "image_organique"}              # les autres formats sont des vidéos
CAMPAIGN = "wooplans_contenu"


def build_link(platform: str, fmt: str, video_id: str, base: str = OFFER_URL) -> str:
    if platform not in PLATFORMS:
        raise ValueError(f"plateforme inconnue : {platform}")
    if fmt not in FORMATS:
        raise ValueError(f"format inconnu : {fmt}")
    params = {
        "utm_source": platform,
        "utm_medium": MEDIUMS.get(fmt, "video_organique"),
        "utm_campaign": CAMPAIGN,
        "utm_content": f"{FORMATS[fmt]}_{video_id}",
    }
    return f"{base}?{urlencode(params)}"


def all_links(fmt: str, video_id: str) -> dict:
    return {p: build_link(p, fmt, video_id) for p in PLATFORMS}


def free_link(platform: str) -> str:
    """Lien court vers le catalogue gratuit : seulement l'origine de la visite (ex. …/catalogue?utm_source=facebook)."""
    if platform not in PLATFORMS:
        raise ValueError(f"plateforme inconnue : {platform}")
    return f"{FREE_CATALOGUE_URL}?utm_source={platform}"
