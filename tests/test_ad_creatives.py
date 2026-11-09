import json
from pathlib import Path

from PIL import Image

from tools import make_ad_creatives as mac

ROOT = Path(__file__).resolve().parent.parent / "creatives" / "top7"


def test_spec_et_visuels(tmp_path):
    spec = json.loads((ROOT / "spec.json").read_text(encoding="utf-8"))
    assert spec["price_fcfa"] == 14900
    assert len(spec["plans"]) == 7
    p = spec["plans"][1]
    out = mac.make(p, ROOT, spec["price_fcfa"])
    assert Image.open(out).size == (1080, 1350)


def test_textes_sans_urgence():
    from wooplans.guardrails import check_copy
    p = {"name": "Villa V4-036", "bedrooms": 4, "bathrooms": 2, "surface": 233}
    assert check_copy(" | ".join(mac.lines_for(p, 14900)), allowed_amounts=[14900]) == []


def test_offre_catalogue_offert():
    assert mac.offer_label(14900) == "Plan + devis du modèle"
    assert "Catalogue Premium offert" in mac.offer_label(39000)
    from wooplans.guardrails import check_copy
    p = {"name": "Villa V4-036", "bedrooms": 4, "bathrooms": 2, "surface": 233}
    assert check_copy(" | ".join(mac.lines_for(p, 29000)), allowed_amounts=[29000]) == []
