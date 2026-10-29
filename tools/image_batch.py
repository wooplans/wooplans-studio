"""Lot hebdomadaire de posts images Facebook : préparation (aperçu pour Tao) puis programmation (après son accord).

  python tools/image_batch.py plan     batches/images/<lot>    # lit <lot>/PLAN, écrit batch.json, batch.md, apercu-N.jpg
  python tools/image_batch.py schedule batches/images/<lot>    # lit <lot>/batch.json, programme sur Zernio (page Facebook WooPlans)

<lot>/PLAN : {"start": "2026-10-20", "days": 7, "slots": ["07:30","12:30","19:00"], "seed": 1}   (slots, seed optionnels)
  Options : "cats": ["duplex","villa","villa","duplex"] (catégorie de chaque créneau), "patterns": ["single","single","album","album"],
  "media": "local" = images déjà filigranées (JPEG) rangées dans <lot>/media/<code>/1.jpg, 2.jpg… (originaux propres + filigranes WooPlans,
  voir tools/brand_media.py) au lieu des rendus filigranés du site.
`plan` ne programme RIEN. `schedule` n'est lancé (workflow image-batch, fichier <lot>/APPROVED) qu'après l'accord explicite de Tao.
Pour retirer ou corriger un post avant l'accord : mettre "skip": true ou éditer "caption" dans batch.json.
Les rendus viennent de la fiche publique du plan (https://www.wooplans.com/catalogue/<slug>) ; chaque légende passe par check_copy.
"""
import io
import json
import re
import sys
import tempfile
from datetime import date
from pathlib import Path

import requests
from PIL import Image

from wooplans.image_posts import (DEFAULT_SLOTS, FMT, TZ, build_batch, day_label, base, load_plans, usage_from_registry)
from wooplans.image_tools import contact_sheet, prepare_image
from wooplans.registry import claim, key, set_state, _load, REGISTRY

SITE = "https://www.wooplans.com"
UA = {"User-Agent": "Mozilla/5.0 (compatible; WooPlansStudio/1.0)"}
WATERMARK = False                                  # les rendus du catalogue portent déjà le filigrane wooplans.com : pas de second filigrane
PAGE = 6                                           # posts par planche d'aperçu (3 colonnes × 2 lignes)


def is_local(ref: str) -> bool:
    return not ref.startswith("http")


def local_images(lot: Path):
    """Images prêtes à publier d'un lot « media: local » : code → ['media/<code>/1.jpg', …] (ordre des numéros)."""
    def images_for(code: str) -> list:
        d = lot / "media" / code
        return [f"media/{code}/{f.name}" for f in sorted(d.glob("*.jpg"), key=lambda f: int(f.stem))] if d.is_dir() else []
    return images_for


def download(url: str) -> bytes:
    r = requests.get(url, headers=UA, timeout=60)
    r.raise_for_status()
    return r.content


THUMB = re.compile(r'aria-label="Voir l(?:\'|&#x27;)image \d+"[^>]*><img[^>]*?src="(/media/[^"]+)"')


def parse_gallery(html: str, code: str) -> list:
    """Rendus de la galerie d'une fiche, dans l'ordre (le premier est la couverture).
    Les miniatures « Voir l'image N » listent exactement les images du plan ; les plans récents sont sous
    /media/public/<code>/, les plus anciens sous /media/upload-framer-<hash>.webp. Repli : dossier du plan."""
    found = THUMB.findall(html)
    if not found:
        found = re.findall(r"(/media/public/%s/[A-Za-z0-9_\-.]+?\.(?:webp|jpe?g|png))" % re.escape(code.lower()), html)
    return list(dict.fromkeys(SITE + p for p in found))


def fetch_page_images(plan: dict) -> list:
    """URL des rendus publics d'un plan (https://www.wooplans.com/catalogue/<slug>), couverture en premier."""
    r = requests.get(f"{SITE}/catalogue/{plan['slug']}", headers=UA, timeout=60)
    r.raise_for_status()
    return parse_gallery(r.text, plan["code"])


def cmd_plan(lot: Path, fetch_images=fetch_page_images, fetch=download) -> int:
    cfg = json.loads((lot / "PLAN").read_text(encoding="utf-8"))
    if cfg.get("media") == "local":
        fetch_images = lambda p: local_images(lot)(p["code"])
        fetch = lambda ref: (lot / ref).read_bytes() if is_local(ref) else download(ref)
    plans = load_plans()
    by_code = {p["code"]: p for p in plans}
    count, used = usage_from_registry()

    def images_for(code):
        try:
            return fetch_images(by_code[code])
        except Exception as e:                       # fiche injoignable : on passe au plan suivant
            print(f"  ! {code} : {e}")
            return []

    posts = build_batch(plans, date.fromisoformat(cfg["start"]), int(cfg.get("days", 7)), images_for,
                        usage=count, used_imgs=used, slots=cfg.get("slots", DEFAULT_SLOTS), seed=int(cfg.get("seed", 0)),
                        cats=cfg.get("cats"), patterns=cfg.get("patterns"))
    (lot / "batch.json").write_text(json.dumps({"timezone": TZ, "posts": posts}, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

    md = [f"# Lot du {cfg['start']} · {len(posts)} posts\n"]
    items = []
    for p in posts:
        label = f"{p['kind']} ({len(p['images'])} images)" if p["kind"] == "album" else "1 image"
        md += [f"## {day_label(p['when'])} · {p['name']} · {label}", "", p["caption"], ""]
        try:
            items.append((Image.open(io.BytesIO(fetch(p["images"][0]))), day_label(p["when"]), f"{p['code']} · {label}"))
        except Exception as e:
            print(f"  ! aperçu {p['id']} : {e}")
    (lot / "batch.md").write_text("\n".join(md), encoding="utf-8")
    for i in range(0, len(items), PAGE):
        contact_sheet(items[i:i + PAGE], lot / f"apercu-{i // PAGE + 1}.jpg")
    print(f"{len(posts)} posts préparés ({len(items)} aperçus) dans {lot}")
    return 0 if posts else 1


def _post(client, body: dict, idem: str) -> dict:
    r = requests.post(f"{client.api_url}/posts", json=body, headers=dict(client.headers, **{"Idempotency-Key": idem}), timeout=120)
    print(r.status_code, r.text[:300])
    r.raise_for_status()
    j = r.json()
    return j.get("post", j)


def schedule_batch(lot: Path, client, fb_account: str, fetch=download, post=_post, registry=None) -> int:
    batch = json.loads((lot / "batch.json").read_text(encoding="utf-8"))
    failures = 0
    for p in batch["posts"]:
        if p.get("skip") or p.get("etat") == "programme":
            continue
        angle = f"{p['kind']}:" + "+".join(base(u) for u in p["images"])
        if not claim(FMT, p["code"], angle, path=registry):
            if _load(registry or REGISTRY).get(key(FMT, p["code"], angle), {}).get("etat") == "programme":
                p["etat"] = "programme"
                continue
        try:
            media = []
            with tempfile.TemporaryDirectory() as tmp:
                for i, u in enumerate(p["images"]):
                    f = Path(tmp) / f"{p['id']}-{i}.jpg"
                    # image locale du lot : déjà en JPEG final avec les filigranes WooPlans, envoyée telle quelle
                    f.write_bytes((lot / u).read_bytes() if is_local(u) else prepare_image(fetch(u), watermark=WATERMARK))
                    media.append({"type": "image", "url": client.upload_media(f, "image/jpeg")})
            body = {"content": p["caption"], "mediaItems": media, "scheduledFor": p["when"], "timezone": p["timezone"],
                    "platforms": [{"platform": "facebook", "accountId": fb_account}]}
            res = post(client, body, f"wooplans-{FMT}-{p['id']}")
            set_state(FMT, p["code"], "programme", angle, path=registry, post_id=res.get("_id") or res.get("id"),
                      quand=p["when"], fuseau=p["timezone"], images=[base(u) for u in p["images"]])
            p["etat"] = "programme"
        except Exception as e:
            failures += 1
            print(f"  ! {p['id']} {p['code']} : {e}")
    (lot / "batch.json").write_text(json.dumps(batch, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    done = sum(1 for p in batch["posts"] if p.get("etat") == "programme")
    print(f"{done} posts programmés, {failures} échec(s)")
    return 1 if failures else 0


def cmd_schedule(lot: Path) -> int:
    from tools.publish_zernio import wooplans_accounts
    from wooplans.zernio_client import ZernioClient
    client = ZernioClient()
    acc = wooplans_accounts(client)
    if "facebook" not in acc:
        print("Page Facebook WooPlans introuvable dans Zernio")
        return 1
    return schedule_batch(lot, client, acc["facebook"])


def main(argv) -> int:
    if len(argv) != 3 or argv[1] not in ("plan", "schedule"):
        print(__doc__)
        return 2
    lot = Path(argv[2])
    return cmd_plan(lot) if argv[1] == "plan" else cmd_schedule(lot)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
