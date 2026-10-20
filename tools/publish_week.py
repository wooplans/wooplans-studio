"""Programme sur Zernio (Facebook Reel + YouTube Short) les vidéos de week/SCHEDULE.json, créneau par créneau.
Lancé par le workflow publish-week, SEULEMENT après l'accord de Tao. Idempotent : registre + Idempotency-Key, vignette créée avant tout post.
TikTok @wooplans n'est pas sur Zernio : légendes dans le fichier, programmation par le connecteur WoopSocial."""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import requests

from tools.publish_zernio import wooplans_accounts
from wooplans.guardrails import check_copy
from wooplans.image_posts import load_plans
from wooplans.registry import claim, set_state, _load, key, REGISTRY
from wooplans.zernio_client import ZernioClient
from wooplans.reel3d import fcfa

ROOT = Path(__file__).resolve().parents[1]


def thumb_for(item: dict, tmp: Path) -> Path:
    job = tmp / item["id"]
    job.mkdir(parents=True, exist_ok=True)
    out = job / "thumb.jpg"
    if item["kind"] == "tour":
        src = ROOT / "visite_plan/jobs" / item["id"]
        for f in ("plan.png", "meta.json"):
            shutil.copy(src / f, job / f)
    else:
        from tools.image_batch import download, fetch_page_images
        plan = next(p for p in load_plans() if p["code"] == item["id"])
        url = fetch_page_images(plan)[0]
        (job / "facade.png").write_bytes(download(url))
        (job / "bump.json").write_text(json.dumps({"target": plan["estimate_total"]}), encoding="utf-8")
        (job / "PUBLISH.json").write_text(json.dumps({"thumbnail": {
            "title": f"Combien coûte {'cette villa' if plan['category'].lower().startswith('villa') else 'ce duplex'} ?",
            "badge": fcfa(plan["estimate_total"]) + " FCFA", "chip": f"{plan['bedrooms']} chambres · {plan['surface']} m²"}}), encoding="utf-8")
    subprocess.run([sys.executable, str(ROOT / "tools/make_thumbnail.py"), str(job), str(out)], check=True, cwd=ROOT)
    return out


def main() -> int:
    cfg = json.loads((ROOT / "week/SCHEDULE.json").read_text(encoding="utf-8"))
    client = ZernioClient()
    acc = wooplans_accounts(client)
    print("comptes WooPlans :", acc)
    if "facebook" not in acc or "youtube" not in acc:
        print("comptes manquants")
        return 1
    plans = {p["code"]: p for p in load_plans()}
    tmp, fail = Path(tempfile.mkdtemp()), 0
    for it in cfg["items"]:
        fmt = "R" if it["kind"] == "reel" else "A"
        allowed = [plans[it["id"]]["estimate_total"]] if it["kind"] == "reel" else []
        texts = [it["facebook"]["caption"], it["youtube"]["title"], it["youtube"]["description"]]
        bad = [p for t in texts for p in check_copy(t, allowed)] + (["cpbook"] if "cpbook" in " ".join(texts) else [])
        if bad:
            print(it["id"], "texte refusé :", bad); fail += 1; continue
        if not claim(fmt, it["id"]) and _load(REGISTRY).get(key(fmt, it["id"]), {}).get("etat") == "programme":
            print(it["id"], "déjà programmée"); continue
        video = ROOT / it["video"]
        thumb = thumb_for(it, tmp)
        media = {"type": "video", "url": client.upload_media(video, "video/mp4"), "thumbnail": client.upload_media(thumb, "image/jpeg")}
        platforms = [
            {"platform": "facebook", "accountId": acc["facebook"], "customContent": it["facebook"]["caption"], "platformSpecificData": {"contentType": "reel"}},
            {"platform": "youtube", "accountId": acc["youtube"], "customContent": it["youtube"]["description"],
             "platformSpecificData": {"title": it["youtube"]["title"], "visibility": "public", "madeForKids": False}}]
        body = {"content": it["facebook"]["caption"], "mediaItems": [media], "platforms": platforms,
                "scheduledFor": it["scheduled_for"], "timezone": cfg["timezone"]}
        r = requests.post(f"{client.api_url}/posts", json=body, headers=dict(client.headers, **{"Idempotency-Key": f"wooplans-{fmt}-{it['id']}"}), timeout=120)
        print(it["id"], it["scheduled_for"], r.status_code, r.text[:300])
        if r.status_code >= 300:
            fail += 1; continue
        post = r.json().get("post", r.json())
        set_state(fmt, it["id"], "programme", post_id=post.get("_id") or post.get("id"), quand=it["scheduled_for"], fuseau=cfg["timezone"])
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
