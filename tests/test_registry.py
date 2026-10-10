from wooplans.registry import claim, set_state


def test_no_duplicates(tmp_path):
    p = tmp_path / "v.json"
    assert claim("A", "P01", path=p) is True
    assert claim("A", "P01", path=p) is False
    assert claim("B", "P01", "erreur toiture", path=p) is True
    assert claim("B", "P01", "Erreur Toiture", path=p) is False
    set_state("A", "P01", "produit", path=p)
