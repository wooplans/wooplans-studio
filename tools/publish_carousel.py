"""Publie un carrousel d'images sur la page Facebook WooPlans via Zernio (lancé par le workflow publish-carousel).

  python tools/publish_carousel.py batches/carousel/<id>

Dossier : images *.jpg (ordre alphabétique) + caption.txt. Texte passé par check_copy ; compte wooplanscatalogue uniquement ;
idempotence = id du dossier ; publication immédiate (ou PUBLISH.json {"scheduled_for","timezone"} si présent).
"""
import json
import sys
from pathlib import Path

import requests

from tools.publish_zernio import wooplans_accounts
from wooplans.guardrails import check_copy
from wooplans.zernio_client import ZernioClient


def main() -> int:
    d = Path(sys.argv[1])
    cap = (d / "caption.txt").read_text(encoding="utf-8").strip()
    allowed = json.loads((d / "allowed.json").read_text()) if (d / "allowed.json").exists() else []
    problems = check_copy(cap, allowed)
    if problems or "cpbook.wooplans.com" in cap:
        print("Texte refusé :", problems)
        return 1
    imgs = sorted(d.glob("*.jpg"))
    if not imgs:
        print("Aucune image")
        return 1
    client = ZernioClient()
    fb = wooplans_accounts(client).get("facebook")
    if not fb:
        print("Page wooplanscatalogue introuvable")
        return 1
    media = [{"type": "image", "url": client.upload_media(f, "image/jpeg")} for f in imgs]
    body = {"content": cap, "mediaItems": media, "platforms": [{"platform": "facebook", "accountId": fb}]}
    cfg = d / "PUBLISH.json"
    if cfg.exists():
        c = json.loads(cfg.read_text())
        body.update({"scheduledFor": c["scheduled_for"], "timezone": c["timezone"]})
    else:
        body["publishNow"] = True
    r = requests.post(f"{client.api_url}/posts", json=body,
                      headers=dict(client.headers, **{"Idempotency-Key": f"wooplans-carousel-{d.name}"}), timeout=180)
    print(r.status_code, r.text[:1500])
    r.raise_for_status()
    return 0


if __name__ == "__main__":
    sys.exit(main())
