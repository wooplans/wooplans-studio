"""Vérifie que les 3 pages WooPlans sont connectées à Zernio et qu'aucun compte Kilabi n'est utilisé.

  python -m wooplans.zernio_check
"""
import sys

from wooplans.settings import FORBIDDEN_ZERNIO_ACCOUNTS
from wooplans.zernio_client import ZernioClient

NEEDED = {"facebook": "wooplanscatalogue", "youtube": "wooplans", "tiktok": "wooplans"}


def main() -> int:
    accounts = ZernioClient().get_accounts()
    found = {}
    for a in accounts:
        plat = (a.get("platform") or "").lower()
        name = (a.get("username") or a.get("name") or a.get("displayName") or "").lower().lstrip("@")
        aid = a.get("_id") or a.get("id")
        if aid in FORBIDDEN_ZERNIO_ACCOUNTS:
            continue
        if plat in NEEDED and NEEDED[plat] in name.replace(" ", ""):
            found[plat] = aid
    for plat in NEEDED:
        print(f"{plat:9} {'OK  ' + found[plat] if plat in found else 'MANQUANT'}")
    return 0 if len(found) == len(NEEDED) else 1


if __name__ == "__main__":
    sys.exit(main())
