"""Réglages WooPlans. Les clés viennent uniquement de l'environnement (.env local ou secrets GitHub)."""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

ROOT = Path(__file__).resolve().parent.parent

# Offre unique poussée (décision Tao, 10 oct. 2026)
OFFER_URL = "https://cpbook.wooplans.com/digital"
OFFER_PRICE_FCFA = 39000
OFFER_PROMISE = "50+ plans avec leurs vrais devis"
# Plans complets personnalisés, prix fixes (FAQ wooplans.com) ; le prix du catalogue est déduit
FULL_PLANS_FCFA = {"villa": 149000, "duplex": 249000}
PIXEL_ID ="1651374605332302"

# Pages sociales WooPlans (distinctes de Kilabi et de « Secrets D'ébène Studios »)
PAGES = {
    "facebook": "https://www.facebook.com/wooplanscatalogue",
    "youtube": "https://www.youtube.com/@wooplans",
    "tiktok": "https://www.tiktok.com/@wooplans",
}

# Comptes interdits pour tout contenu WooPlans (ids Zernio des comptes Kilabi / Secrets D'ébène)
FORBIDDEN_ZERNIO_ACCOUNTS = {
    "6abcd03345846add02896679",  # facebook : Secrets D'ébène Studios
    "6ac5d2031c95fb892bf281cf",  # facebook : Kilabi
    "6ac6db234396cb4c08cfed0a",  # tiktok : kilabi.explique
}

VOICE_ID = os.environ.get("WOOPLANS_VOICE_ID", "iEagsFvjnTp38icamMSP")  # ElevenLabs « LeTao » (ne pas créer de voix)

ZERNIO_API_KEY = os.environ.get("ZERNIO_API_KEY", "").strip()
ZERNIO_PROFILE_ID = os.environ.get("ZERNIO_PROFILE_ID", "").strip()
ZERNIO_ACCOUNT_ID = os.environ.get("ZERNIO_ACCOUNT_ID", "").strip()
ZERNIO_API_URL = os.environ.get("ZERNIO_API_URL", "https://zernio.com/api/v1").rstrip("/")
