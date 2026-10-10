import pytest
from wooplans.utm import all_links, build_link


def test_link_per_platform():
    l = all_links("A", "V001")
    assert set(l) == {"facebook", "tiktok", "youtube"}
    assert l["tiktok"].startswith("https://cpbook.wooplans.com/digital?")
    assert "utm_source=tiktok" in l["tiktok"] and "utm_content=visite_V001" in l["tiktok"]


def test_bad_input():
    with pytest.raises(ValueError):
        build_link("instagram", "A", "x")
    with pytest.raises(ValueError):
        build_link("facebook", "Z", "x")
