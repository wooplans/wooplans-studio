"""Programme une vidéo de visite sur les pages WooPlans via Zernio (lancé par le workflow publish-zernio).

  python tools/publish_zernio.py visite_plan/jobs/<id>

Lit <job>/PUBLISH.json : {"video": "...mp4", "scheduled_for": "2026-10-19T19:00:00", "timezone": "Africa/Douala",
  "facebook": {"caption": "..."}, "youtube": {"title": "...", "description": "..."}}
N'utilise que les comptes WooPlans (jamais Kilabi / Secrets D'ébène) ; chaque texte passe par check_copy.
"""
import json
import sys
from pathlib import Path

import requests

from wooplans.guardrails import check_copy
from wooplans.registry import claim, set_state
from wooplans.settings import FORBIDDEN_ZERNIO_ACCOUNTS
from wooplans.zernio_client import ZernioClient

NEEDED = {"facebook": "wooplanscatalogue", "youtube": "wooplans", "tiktok": "wooplans"}


def wooplans_accounts(client: ZernioClient) -> dict:
    found = {}
    for a in client.get_accounts():
        plat = (a.get("platform") or "").lower()
        name = (a.get("username") or a.get("name") or a.get("displayName") or "").lower().lstrip("@").replace(" ", "")
        aid = a.get("_id") or a.get("id")
        if aid not in FORBIDDEN_ZERNIO_ACCOUNTS and plat in NEEDED and NEEDED[plat] in name:
            found[plat] = aid
    return found


def main() -> int:
    job = Path(sys.argv[1])
    cfg = json.loads((job / "PUBLISH.json").read_text(encoding="utf-8"))
    texts = [cfg["facebook"]["caption"], cfg["youtube"]["title"], cfg["youtube"]["description"]]
    problems = [p for t in texts for p in check_copy(t)]
    if problems:
        print("Texte refusé :", problems)
        return 1
    client = ZernioClient()
    acc = wooplans_accounts(client)
    print("comptes WooPlans :", acc)
    platforms = []
    if "facebook" in acc:
        platforms.append({"platform": "facebook", "accountId": acc["facebook"], "customContent": cfg["facebook"]["caption"],
                          "platformSpecificData": {"contentType": "reel"}})
    if "youtube" in acc:
        platforms.append({"platform": "youtube", "accountId": acc["youtube"], "customContent": cfg["youtube"]["description"],
                          "platformSpecificData": {"title": cfg["youtube"]["title"], "visibility": "public", "madeForKids": False}})
    if "tiktok" in acc and cfg.get("tiktok"):
        platforms.append({"platform": "tiktok", "accountId": acc["tiktok"], "customContent": cfg["tiktok"]["caption"]})
    if not platforms:
        print("Aucun compte WooPlans connecté")
        return 1
    plan = job.name
    claim("A", plan)
    url = client.upload_media(cfg["video"], "video/mp4")
    body = {"content": cfg["facebook"]["caption"], "mediaItems": [{"type": "video", "url": url}], "platforms": platforms,
            "scheduledFor": cfg["scheduled_for"], "timezone": cfg["timezone"]}
    r = requests.post(f"{client.api_url}/posts", json=body, headers=client.headers, timeout=120)
    print(r.status_code, r.text[:1500])
    r.raise_for_status()
    post = r.json().get("post", r.json())
    set_state("A", plan, "programme", post_id=post.get("_id") or post.get("id"), quand=cfg["scheduled_for"],
              fuseau=cfg["timezone"], plateformes=[p["platform"] for p in platforms])
    return 0


if __name__ == "__main__":
    sys.exit(main())
