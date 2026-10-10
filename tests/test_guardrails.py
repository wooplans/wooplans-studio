from wooplans.guardrails import amounts, check_copy


def test_expire_forbidden():
    assert check_copy("Attention, l'offre expire dans 3 heures !")
    assert check_copy("Plus que 2 heures pour en profiter")
    assert not check_copy("Prix actuel : 39 000 FCFA.")


def test_amounts_sourced():
    assert amounts("Devis : 18 500 000 FCFA et 39 000 F CFA") == [18500000, 39000]
    assert check_copy("Cette villa coûte 18 500 000 FCFA") != []
    assert check_copy("Cette villa coûte 18 500 000 FCFA", allowed_amounts=[18500000]) == []
