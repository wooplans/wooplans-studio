"""Programme une vidéo de visite sur les pages WooPlans via Zernio (lancé par le workflow publish-zernio).

  python tools/publish_zernio.py visite_plan/jobs/<id>

Lit <job>/PUBLISH.json :
  {"video": "visite_plan/out/<id>.mp4", "scheduled_for": "2026-10-19T19:00:00", "timezone": "Africa/Douala",
   "thumbnail": {"title": "...", "badge": "...", "chip": "..."},                      (optionnel : voir make_thumbnail.py)
   "facebook": {"caption": "..."}, "youtube": {"title": "...", "description": "..."},
   "tiktok": {"caption": "..."}                                                      (seulement si TikTok @wooplans est connecté à Zernio)}
- vignette créée AVANT de publier (règle du 16 oct.), envoyée comme couverture du Reel Facebook (YouTube Shorts : pas de vignette perso) ;
- n'utilise que les comptes WooPlans (jamais Kilabi / Secrets D'ébène) ; chaque texte passe par check_copy ;
- clé d'idempotence = id de la vidéo : un second lancement ne programme pas un doublon.
"""
import json
import subprocess
import sys
from pathlib import Path

import requests

from wooplans.guardrails import check_copy
from wooplans.registry import claim, set_state
from wooplans.settings import FORBIDDEN_ZERNIO_ACCOUNTS
from wooplans.zernio_client import ZernioClient

NEEDED = {"facebook": "wooplanscatalogue", "youtube": "wooplans", "tiktok": "wooplans"}
ROOT = Path(__file__).resolve().parents[1]


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
    if cfg.get("tiktok"):
        texts.append(cfg["tiktok"]["caption"])
    allowed = []
    if (job / "bump.json").exists():                       # total « clé en main » du devis (source de vérité)
        B = json.loads((job / "bump.json").read_text(encoding="utf-8"))
        allowed = [v for v in (B.get("target"), B.get("gros"), B.get("fin")) if v]
    problems = [p for t in texts for p in check_copy(t, allowed)]
    if problems:
        print("Texte refusé :", problems)
        return 1
    if "cpbook.wooplans.com" in " ".join(texts):
        print("Ancien lien du catalogue interdit : utiliser https://wooplans.com/catalogue-premium")
        return 1
    video = Path(cfg["video"])
    if not video.is_file():
        print("Vidéo introuvable :", video)
        return 1

    thumb = job / "thumb.jpg"                              # vignette obligatoire
    if not thumb.exists():
        subprocess.run([sys.executable, str(ROOT / "tools" / "make_thumbnail.py"), str(job), str(thumb)], check=True, cwd=ROOT)

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
    if not claim("A", plan):                               # déjà réservée : ne reprogramme pas une vidéo déjà programmée
        from wooplans.registry import _load, key, REGISTRY
        if _load(REGISTRY).get(key("A", plan), {}).get("etat") == "programme":
            print(f"{plan} est déjà programmée (registre) : rien à faire")
            return 0
    media = {"type": "video", "url": client.upload_media(video, "video/mp4"),
             "thumbnail": client.upload_media(thumb, "image/jpeg")}
    body = {"content": cfg["facebook"]["caption"], "mediaItems": [media], "platforms": platforms,
            "scheduledFor": cfg["scheduled_for"], "timezone": cfg["timezone"]}
    headers = dict(client.headers, **{"Idempotency-Key": f"wooplans-{plan}"})
    r = requests.post(f"{client.api_url}/posts", json=body, headers=headers, timeout=120)
    print(r.status_code, r.text[:1500])
    r.raise_for_status()
    post = r.json().get("post", r.json())
    set_state("A", plan, "programme", post_id=post.get("_id") or post.get("id"), quand=cfg["scheduled_for"],
              fuseau=cfg["timezone"], plateformes=[p["platform"] for p in platforms])
    return 0


if __name__ == "__main__":
    sys.exit(main())
