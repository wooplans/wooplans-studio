import io
import json
from datetime import date
from pathlib import Path

import pytest
from PIL import Image

from tools import image_batch
from wooplans.guardrails import check_copy
from wooplans.image_posts import (ALBUM_SIZE, TEMPLATES, base, build_batch, caption, fcfa, load_plans)
from wooplans.image_tools import contact_sheet, prepare_image
from wooplans.registry import _load
from wooplans.utm import build_link

PLANS = load_plans()


def fake_images(code):
    return [f"https://www.wooplans.com/media/public/{code.lower()}/{i}-img{i}.webp" for i in range(6)]


def png_bytes(size=(1200, 800), color=(120, 160, 200)):
    out = io.BytesIO()
    Image.new("RGB", size, color).save(out, "WEBP")
    return out.getvalue()


def test_plans_source_of_truth():
    assert len(PLANS) >= 50
    codes = [p["code"] for p in PLANS]
    assert len(codes) == len(set(codes))
    for p in PLANS:
        assert p["category"] in ("villa", "duplex") and p["slug"].endswith(p["code"].lower())
        assert p["bedrooms"] > 0 and p["surface"] > 0 and p["estimate_total"] > 0


def test_every_caption_passes_guardrails():
    from wooplans.image_posts import budget_range
    for p in PLANS:
        for i in range(len(TEMPLATES)):
            for kind in ("single", "album"):
                name, text = caption(p, i, kind)
                low, high = budget_range(p)
                assert check_copy(text, [p["estimate_total"], low, high]) == []
                assert f"{fcfa(low)} – {fcfa(high)} FCFA" in text                     # fourchette de budget affichée
                assert text.count("https://") == 1 and "https://wooplans.com/catalogue?utm_source=facebook" in text
                assert "premium" not in text.lower() and "39 000" not in text and "utm_medium" not in text
                assert "cpbook" not in text and "expire" not in text.lower()
                assert ("Faites défiler" in text) == (kind == "album")


def test_caption_structure():
    p = next(p for p in PLANS if p["land_area"])
    text = caption(p, 0)[1]
    blocs = text.split("\n\n")
    assert len(blocs) == 5                                                          # accroche, fiche, engagement, CTA, hashtags
    assert blocs[1].splitlines()[0].startswith(f"🏠 {p['name']} · {p['bedrooms']} chambres")
    assert f"Surface : {p['surface']} m²" in blocs[1] and f"Terrain prévu : {p['land_area']} m²" in blocs[1]
    assert blocs[3].splitlines()[1] == "https://wooplans.com/catalogue?utm_source=facebook"


def test_budget_range_matches_catalogue():
    from wooplans.image_posts import budget_range
    by = {p["code"]: p for p in PLANS}
    assert budget_range(by["D4-001"]) == (86_200_000, 105_300_000)                   # fourchettes affichées sur le catalogue
    assert budget_range(by["V3-002"]) == (11_300_000, 13_800_000)
    assert budget_range(by["D4-004"]) == (50_700_000, 62_000_000)


def test_guardrail_catches_a_wrong_amount():
    p = PLANS[0]
    text = caption(p, 0)[1].replace(fcfa(budget_range_high(p)), "1 234 567")
    assert check_copy(text, [p["estimate_total"]])                    # montant non sourcé → refusé


def budget_range_high(p):
    from wooplans.image_posts import budget_range
    return budget_range(p)[1]


def test_french_agreement():
    villa = next(p for p in PLANS if p["category"] == "villa")
    duplex = next(p for p in PLANS if p["category"] == "duplex")
    assert "Cette villa de" in caption(villa, 0)[1] and "une villa de" in caption(villa, 2)[1]
    assert "Ce duplex de" in caption(duplex, 0)[1] and "un duplex de" in caption(duplex, 2)[1]
    assert "de plain-pied" in caption(villa, 0)[1] and "2 niveaux" in caption(duplex, 0)[1]


def test_terrain_line_skipped_without_land():
    p = next(p for p in PLANS if not p["land_area"])
    assert all("Terrain prévu" not in caption(p, i)[1] for i in range(len(TEMPLATES)))


def test_utm_image_medium_and_video_unchanged():
    assert "utm_medium=image_organique" in build_link("facebook", "I", "V4-001")
    assert "utm_medium=video_organique" in build_link("facebook", "A", "V001")


def test_batch_shape_and_rules():
    posts = build_batch(PLANS, date(2026, 10, 20), 7, fake_images, seed=1)
    assert len(posts) == 21
    for d in {p["when"][:10] for p in posts}:
        day = [p for p in posts if p["when"].startswith(d)]
        assert len(day) == 3 and len({p["code"] for p in day}) == 3
        assert [p["when"][11:16] for p in day] == ["07:30", "12:30", "19:00"]
        assert [p["kind"] for p in day] == ["single", "album", "single"]
    for p in posts:
        assert p["kind"] == "single" and len(p["images"]) == 1 or 2 <= len(p["images"]) <= ALBUM_SIZE
        assert p["timezone"] == "Africa/Douala" and p["skip"] is False
    cats = [next(x["category"] for x in PLANS if x["code"] == p["code"]) for p in posts]
    assert sum(a == b for a, b in zip(cats, cats[1:])) <= 3            # alternance villa / duplex
    assert len({p["code"] for p in posts}) >= 18                       # les plans tournent, pas de martelage
    assert posts == build_batch(PLANS, date(2026, 10, 20), 7, fake_images, seed=1)     # déterministe


def test_used_images_not_reused_and_counts_respected():
    usage = {p["code"]: 5 for p in PLANS}
    usage["V4-001"] = 0                                                # le moins publié passe en premier
    used = {"V4-001": {base(u) for u in fake_images("V4-001")[:3]}}
    posts = build_batch(PLANS, date(2026, 10, 20), 1, fake_images, usage=usage, used_imgs=used, seed=2)
    first = posts[0]
    assert first["code"] == "V4-001"
    assert all(base(u) not in used["V4-001"] for u in first["images"])


def test_plan_without_images_is_skipped():
    posts = build_batch(PLANS, date(2026, 10, 20), 1, lambda c: [] if c.startswith("D") else fake_images(c), seed=3)
    assert posts and all(p["code"].startswith("V") for p in posts)


def test_prepare_image_resizes_and_watermarks():
    plain = Image.open(io.BytesIO(prepare_image(png_bytes((3000, 2000)), watermark=False)))
    marked = Image.open(io.BytesIO(prepare_image(png_bytes((3000, 2000)), watermark=True)))
    assert plain.format == "JPEG" and max(plain.size) == 1600 and marked.size == plain.size
    assert plain.tobytes() != marked.tobytes()                         # le filigrane est bien appliqué


def test_contact_sheet(tmp_path):
    im = Image.new("RGB", (800, 600), "gray")
    out = tmp_path / "a.jpg"
    contact_sheet([(im, "lun. 20/10 · 07:30", "V4-001 · 1 image")] * 5, out)
    assert Image.open(out).width == 1080


def test_plan_command_writes_batch_and_previews(tmp_path):
    lot = tmp_path / "2026-10-20"
    lot.mkdir()
    (lot / "PLAN").write_text(json.dumps({"start": "2026-10-20", "days": 2, "seed": 1}))
    rc = image_batch.cmd_plan(lot, fetch_images=lambda p: fake_images(p["code"]), fetch=lambda u: png_bytes())
    assert rc == 0
    b = json.loads((lot / "batch.json").read_text())
    assert len(b["posts"]) == 6 and (lot / "batch.md").read_text().startswith("# Lot du 2026-10-20")
    assert (lot / "apercu-1.jpg").is_file()


class FakeClient:
    api_url = "https://zernio.test/api/v1"
    headers = {}

    def __init__(self):
        self.uploads = []

    def upload_media(self, path, content_type=None):
        data = Path(path).read_bytes()
        assert Image.open(io.BytesIO(data)).format == "JPEG"
        self.uploads.append(Path(path).name)
        return f"https://cdn.test/{Path(path).name}"


def test_schedule_is_idempotent_and_records_registry(tmp_path):
    lot = tmp_path / "lot"
    lot.mkdir()
    posts = build_batch(PLANS, date(2026, 10, 20), 1, fake_images, seed=1)
    posts[1]["skip"] = True                                            # un post retiré par Tao
    (lot / "batch.json").write_text(json.dumps({"timezone": "Africa/Douala", "posts": posts}))
    reg = tmp_path / "videos.json"
    sent = []

    def fake_post(client, body, idem):
        sent.append((body, idem))
        return {"_id": f"post{len(sent)}"}

    c = FakeClient()
    assert image_batch.schedule_batch(lot, c, "FBACC", fetch=lambda u: png_bytes(), post=fake_post, registry=reg) == 0
    assert len(sent) == 2                                              # le post « skip » n'est pas programmé
    body, idem = sent[0]
    assert body["platforms"] == [{"platform": "facebook", "accountId": "FBACC"}]
    assert body["scheduledFor"] == posts[0]["when"] and body["timezone"] == "Africa/Douala"
    assert all(m["type"] == "image" for m in body["mediaItems"]) and idem.startswith("wooplans-I-")
    states = [e["etat"] for e in _load(reg).values()]
    assert states == ["programme", "programme"]
    # second passage : rien n'est reprogrammé
    assert image_batch.schedule_batch(lot, c, "FBACC", fetch=lambda u: png_bytes(), post=fake_post, registry=reg) == 0
    assert len(sent) == 2


def test_schedule_failure_is_reported_and_retryable(tmp_path):
    lot = tmp_path / "lot"
    lot.mkdir()
    posts = build_batch(PLANS, date(2026, 10, 20), 1, fake_images, seed=1)[:1]
    (lot / "batch.json").write_text(json.dumps({"posts": posts}))
    reg = tmp_path / "videos.json"

    def boom(*a, **k):
        raise RuntimeError("zernio down")

    assert image_batch.schedule_batch(lot, FakeClient(), "FB", fetch=lambda u: png_bytes(), post=boom, registry=reg) == 1
    ok = []
    assert image_batch.schedule_batch(lot, FakeClient(), "FB", fetch=lambda u: png_bytes(),
                                      post=lambda c, b, i: ok.append(1) or {"_id": "x"}, registry=reg) == 0
    assert ok == [1]


HTML_NEW = ('<button aria-label="Voir l&#x27;image 1"><img src="/media/public/v4-001/a1.webp" alt="" /></button>'
            '<button aria-label="Voir l&#x27;image 2"><img src="/media/public/v4-001/a2.webp" alt="" /></button>'
            '<img src="/media/public/d5-011/autre-plan-suggere.webp" alt="Duplex">')
HTML_OLD = ('<button aria-label="Voir l&#x27;image 1" class="x"><img src="/media/upload-framer-aaa111.jpg" alt="" /></button>'
            '<button aria-label="Voir l&#x27;image 2" class="x"><img src="/media/upload-framer-bbb222.webp" alt="" /></button>'
            '<img src="/media/public/d5-011/autre-plan-suggere.webp" alt="Duplex">')


def test_parse_gallery_both_storage_styles_and_ignores_suggested_plans():
    new = image_batch.parse_gallery(HTML_NEW, "V4-001")
    old = image_batch.parse_gallery(HTML_OLD, "D4-026")
    assert new == ["https://www.wooplans.com/media/public/v4-001/a1.webp", "https://www.wooplans.com/media/public/v4-001/a2.webp"]
    assert old == ["https://www.wooplans.com/media/upload-framer-aaa111.jpg", "https://www.wooplans.com/media/upload-framer-bbb222.webp"]
    assert all("d5-011" not in u for u in new + old)                                # jamais les images d'un plan suggéré


def test_parse_gallery_fallback_to_plan_folder():
    html = '<img src="/media/public/v4-001/z9.webp"><img src="/media/public/d5-011/x.webp">'
    assert image_batch.parse_gallery(html, "V4-001") == ["https://www.wooplans.com/media/public/v4-001/z9.webp"]


# ---------- lot « 2 duplex + 2 villas par jour », images locales filigranées ----------

CATS = ["duplex", "villa", "villa", "duplex"]
PATS = ["single", "single", "album", "album"]
SLOTS4 = ["07:30", "10:30", "16:30", "19:00"]



def local_fixture(code):
    return [f"media/{code}/{i + 1}.jpg" for i in range(4 if code.endswith(("1", "3", "5", "7", "9")) else 1)]


def test_batch_two_duplex_two_villas_per_day_and_no_repeat():
    posts = build_batch(PLANS, date(2026, 10, 30), 7, local_fixture, slots=SLOTS4, cats=CATS, patterns=PATS, seed=1)
    assert len(posts) == 28 and len({p["code"] for p in posts}) == 28
    by_code = {p["code"]: p for p in PLANS}
    for d in {p["when"][:10] for p in posts}:
        day = [p for p in posts if p["when"].startswith(d)]
        assert [by_code[p["code"]]["category"] for p in day] == CATS
        assert [p["kind"] for p in day] == PATS
        assert [len(p["images"]) > 1 for p in day] == [False, False, True, True]


def test_prepare_brand_watermark_two_marks_and_size():
    from wooplans.image_tools import brand_watermark
    src = png_bytes((2400, 1350), (90, 110, 140))
    plain = Image.open(io.BytesIO(prepare_image(src, watermark=False)))
    marked = Image.open(io.BytesIO(brand_watermark(src)))
    assert marked.format == "JPEG" and marked.size == plain.size == (1600, 900)
    w, h = marked.size
    centre = (w // 2 - 20, h // 2 - 20, w // 2 + 20, h // 2 + 20)
    corner = (w - 80, h - 60, w - 20, h - 20)
    for box in (centre, corner):                                          # logo central ET pastille d'angle présents
        assert marked.crop(box).tobytes() != plain.crop(box).tobytes()


def test_local_media_plan_and_schedule(tmp_path):
    lot = tmp_path / "lot"
    plans = [p for p in PLANS if p["code"] in ("D4-003", "D4-004", "V3-002", "V3-003")]
    for p in plans:
        for i in range(4 if p["code"] in ("D4-004", "V3-003") else 1):
            f = lot / "media" / p["code"] / f"{i + 1}.jpg"
            f.parent.mkdir(parents=True, exist_ok=True)
            Image.new("RGB", (160, 90), "gray").save(f, "JPEG")
    (lot / "PLAN").write_text(json.dumps({"start": "2026-10-30", "days": 1, "slots": SLOTS4, "cats": CATS, "patterns": PATS,
                                          "media": "local"}))
    orig = image_batch.load_plans
    image_batch.load_plans = lambda: plans
    try:
        assert image_batch.cmd_plan(lot) == 0
    finally:
        image_batch.load_plans = orig
    b = json.loads((lot / "batch.json").read_text())["posts"]
    assert [p["code"] for p in b] == ["D4-003", "V3-002", "V3-003", "D4-004"]
    assert all(not u.startswith("http") for p in b for u in p["images"])
    assert (lot / "apercu-1.jpg").is_file()
    sent = []
    c = FakeClient()
    assert image_batch.schedule_batch(lot, c, "FB", fetch=lambda u: (_ for _ in ()).throw(AssertionError("pas de réseau")),
                                      post=lambda cl, body, idem: sent.append(body) or {"_id": "x"}, registry=tmp_path / "r.json") == 0
    assert len(sent) == 4 and [len(s["mediaItems"]) for s in sent] == [1, 1, 4, 4]
