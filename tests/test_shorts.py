import pytest

from tools.new_short import spread
from wooplans import site_api, shorts

PLANS = [
    {"code": "V4-001", "category": "villa", "bedrooms": 4, "surface": 116, "land_area": 250},
    {"code": "V4-002", "category": "villa", "bedrooms": 4, "surface": 155, "land_area": None},
    {"code": "V3-022", "category": "villa", "bedrooms": 3, "surface": 89, "land_area": 250},
    {"code": "D4-004", "category": "duplex", "bedrooms": 4, "surface": 313, "land_area": 350},
]


def test_resolve_codes_types_categories():
    assert shorts.resolve("d4-004, V3-022", PLANS) == ["D4-004", "V3-022"]
    assert shorts.resolve("V4", PLANS) == ["V4-001", "V4-002"]
    assert shorts.resolve("villas", PLANS) == ["V4-001", "V4-002", "V3-022"]
    assert shorts.resolve("duplex V4-001", PLANS) == ["D4-004", "V4-001"]
    assert len(shorts.resolve("tous", PLANS)) == 4


def test_resolve_rejects_unknown():
    with pytest.raises(ValueError):
        shorts.resolve("V9-999", PLANS)
    with pytest.raises(ValueError):
        shorts.resolve("D7", PLANS)


def test_resolve_nouveaux_skips_existing(monkeypatch):
    monkeypatch.setattr(shorts, "has_short", lambda c: c == "V4-001")
    assert shorts.resolve("V4 nouveaux", PLANS) == ["V4-002"]


def test_texts_without_land():
    assert shorts.texts(PLANS[1]) == ("Villa 4 chambres", "155 m²")
    assert shorts.texts(PLANS[3]) == ("Duplex 4 chambres", "313 m² · terrain 350 m²")


def test_spread_keeps_cover_and_covers_gallery():
    assert spread(list(range(3))) == [0, 1, 2]
    picked = spread(list(range(10)))
    assert picked[0] == 0 and len(picked) == 4 and len(set(picked)) == 4 and picked[-1] >= 7


def test_usable_renders_filters():
    big_clean = {"key": "s3", "watermarked": False, "width": 1376}
    index = {"renders": [
        {"position": 1, "cover": False, "original": {"key": "a", "watermarked": False}},
        {"position": 2, "cover": True, "original": {"key": "b", "watermarked": None}},
        {"position": 3, "cover": False, "original": None, "site": big_clean},
        {"position": 4, "cover": False, "original": {"key": "d", "watermarked": True}},
        {"position": 5, "cover": False, "original": {"key": "e", "missing": True}},
        {"position": 6, "cover": False, "original": None, "site": {"key": "s6", "watermarked": True, "width": 1376}},
        {"position": 7, "cover": False, "original": None, "site": {"key": "s7", "watermarked": False, "width": 960}},
    ]}
    got = site_api.usable_renders("X", index)
    assert [r["key"] for r in got] == ["b", "a", "s3"]
    assert [r["source"] for r in got] == ["original", "original", "site"]
