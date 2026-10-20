import re

from wooplans.image_posts import load_plans
from wooplans.reel3d import (OVERLAP, assign_images, bar_length, build_ass, check_scenes, count_steps, fcfa, image_mode, n_bars,
                             pan, scenes, ts)

PLANS = load_plans()
WITH_LAND = next(p for p in PLANS if p.get("land_area") and p["levels"] == 2)
NO_LAND = next(p for p in PLANS if not p.get("land_area"))
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
