from campagnes.guide_des_maisons import pubs
from wooplans.guardrails import check_copy


def test_tous_les_textes_passent_les_garde_fous():
    for text in pubs.all_texts():
        assert check_copy(text, pubs.ALLOWED_AMOUNTS) == [], text


def test_lien_vers_la_page_du_guide_avec_utm():
    link = pubs.ad_link("budget")
    assert link.startswith("https://wooplans.com/guide-des-maisons?")
    assert "utm_campaign=guide_maisons" in link and "utm_content=budget" in link
    assert "cpbook" not in link


def test_jamais_le_livre_imprime_dans_les_pubs():
    for text in pubs.all_texts():
        assert "livre" not in text.lower(), text
