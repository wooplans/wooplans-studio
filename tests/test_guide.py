import json
import re

from tools.build_guide import TRANCHES, check, millions, pages
from wooplans import settings

PLANS = {p["code"]: p for p in json.load(open(settings.ROOT / "data" / "plans.json"))}


def test_guide_has_30_pages_and_20_models_from_plans_json():
    P = pages(PLANS)
    models = [p for p in P if p["kind"] == "model"]
    assert len(P) == 30 and len(models) == 20 and [p['kind'] for p in P[-2:]] == ['cat1', 'cat2']
    assert [m["code"] for m in models] == [c for *_, cs in TRANCHES for c in cs]
    for m in models:
        assert millions(PLANS[m["code"]]["estimate_total"]) in m["estimate"]


def test_guide_texts_pass_guardrails_and_price_is_current_offer():
    P = pages(PLANS)
    assert check(P) == []
    cat = next(p for p in P if p["kind"] == "cat2")
    assert "Prix actuel : 39 000 FCFA" in cat["body"] and "wooplans.com/catalogue-premium" in cat["link"]
    assert not any(re.search(r"cpbook|expire", p["body"], re.I) for p in P)


def test_tranches_match_estimates():
    bounds = [(0, 20e6), (20e6, 40e6), (40e6, 60e6), (60e6, 1e12)]
    for (_, _, _, codes), (lo, hi) in zip(TRANCHES, bounds):
        assert all(lo <= PLANS[c]["estimate_total"] < hi for c in codes)
