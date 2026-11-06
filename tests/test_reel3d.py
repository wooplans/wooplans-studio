import re

from wooplans.image_posts import load_plans
from wooplans.reel3d import (OVERLAP, assign_images, bar_length, build_ass, check_scenes, count_steps, fcfa, image_mode, n_bars,
                             pan, scenes, ts)

PLANS = load_plans()
WITH_LAND = next(p for p in PLANS if p.get("land_area") and p["levels"] == 2)
NO_LAND = dict(WITH_LAND, land_area=None)        # le site renseigne tous les terrains : cas fabriqué
VILLA = next(p for p in PLANS if p["levels"] == 1 and p.get("land_area"))


def test_bar_length_from_tempo():
    assert abs(bar_length(100) - 2.4) < 1e-9


def test_scenes_structure():
    a, b = scenes(WITH_LAND), scenes(NO_LAND)
    assert n_bars(a) == 10 and n_bars(b) == 9                      # la mesure « terrain » saute quand il est inconnu
    assert a[-1].end_card and not a[-1].lines
    assert [s.bar for s in a] == sorted(s.bar for s in a)
    assert any(s.count_to == WITH_LAND["estimate_total"] for s in a)
    assert not any("TERRAIN" in l.text for s in b for l in s.lines)


def test_text_uses_only_plan_facts_and_passes_guardrails():
    for p in PLANS:
        assert check_scenes(scenes(p), p) == []
        txt = " ".join(l.text for s in scenes(p) for l in s.lines)
        assert str(p["surface"]) in txt and f"*{p['bedrooms']}*" in txt


def test_villa_is_single_level_wording():
    assert any("PLAIN-PIED" in l.text for s in scenes(VILLA) for l in s.lines)
    assert any(f"SUR {WITH_LAND['levels']} NIVEAUX" in l.text for s in scenes(WITH_LAND) for l in s.lines)


def test_count_steps_monotonic_and_exact():
    for target in (11_776_000, 42_300_000, 95_760_000):
        v = count_steps(target)
        assert v[-1] == target and v == sorted(v) and v[0] > 0


def test_assign_images_prefers_full_screen_renders():
    sizes = [(1280, 720)] + [(2000, 2000)] * 7
    got = assign_images(10, sizes)
    assert all(mode == "cover" for _, mode in got) and 0 not in [i for i, _ in got]      # le 16:9 flou n'est pas utilisé
    assert assign_images(5, [(1280, 720), (1280, 720)])[0][1] == "blurpad"               # repli quand il n'y a rien d'autre
    assert image_mode((2000, 2000)) == "cover" and image_mode((1280, 720)) == "blurpad" and image_mode((900, 900)) == "blurpad"


def test_pan_alternates_and_stays_inside_image():
    assert pan(0) == (0.15, 0.85) and pan(1) == (0.85, 0.15)
    assert all(0 <= v <= 1 for k in range(6) for v in pan(k))


def test_ass_events_are_valid():
    p, bar, total = WITH_LAND, 2.4, 10 * 2.4 + OVERLAP
    ass = build_ass(scenes(p), p, bar, total)
    events = re.findall(r"^Dialogue: (\d),(\d+:\d\d:\d\d\.\d\d),(\d+:\d\d:\d\d\.\d\d),(\w+),", ass, re.M)
    assert events and ass.count("PlayResX: 1080") == 1 and "PlayResY: 1920" in ass

    def sec(x):
        h, m, s = x.split(":")
        return int(h) * 3600 + int(m) * 60 + float(s)

    assert all(sec(e) > sec(s) for _, s, e, _ in events)
    assert max(sec(e) for _, _, e, st in events if st == "Cap") <= 9 * 2.4                 # aucun texte sur la carte finale
    assert fcfa(p["estimate_total"]) in ass and "estimation indicative" in ass
    assert ass.count("wooplans.com") >= 5 and "\\move(1500," in ass                          # filigrane qui défile


def test_ts_format():
    assert ts(0) == "0:00:00.00" and ts(61.5) == "0:01:01.50" and ts(-3) == "0:00:00.00"


# ---------- offre à l'unité : plan et devis du modèle ----------

def test_plan_devis_scenes_have_no_land_nor_estimate():
    from wooplans.settings import PLAN_DEVIS_PRICE_FCFA
    for p in PLANS:
        sc = scenes(p, "plan_devis")
        txt = " ".join(l.text for s in sc for l in s.lines)
        assert "TERRAIN" not in txt and "{n}" not in txt and not any(s.count_to for s in sc)
        assert "CATALOGUE" not in txt and fcfa(PLAN_DEVIS_PRICE_FCFA) in txt
        assert str(p["surface"]) in txt and f"*{p['bedrooms']}*" in txt
        assert sc[-1].end_card and check_scenes(sc, p) == []


def test_unknown_offer_is_refused():
    import pytest
    with pytest.raises(ValueError):
        scenes(PLANS[0], "cadeau")


def test_plan_devis_end_card_passes_guardrails():
    from tools.make_reel import end_card_texts
    from wooplans.guardrails import check_copy
    from wooplans.settings import PLAN_DEVIS_PRICE_FCFA
    texts = end_card_texts("plan_devis")
    assert not any("Catalogue" in t or "gratuit" in t.lower() for t in texts)
    assert all(check_copy(t, [PLAN_DEVIS_PRICE_FCFA]) == [] for t in texts)


def test_plan_devis_variants_same_facts_and_guardrails():
    from wooplans.reel3d import VARIANTS
    from wooplans.settings import PLAN_DEVIS_PRICE_FCFA
    for v in VARIANTS:
        for p in PLANS:
            sc = scenes(p, "plan_devis", v)
            txt = " ".join(l.text for s in sc for l in s.lines)
            assert "TERRAIN PRÉVU" not in txt and "{n}" not in txt and "CATALOGUE" not in txt
            assert fcfa(PLAN_DEVIS_PRICE_FCFA) in txt and str(p["surface"]) in txt and f"*{p['bedrooms']}*" in txt
            assert sc[-1].end_card and check_scenes(sc, p) == []
            assert [s.bar for s in sc] == list(range(len(sc)))
