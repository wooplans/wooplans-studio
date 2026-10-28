from wooplans.settings import FORBIDDEN_ZERNIO_ACCOUNTS, OFFER_PRICE_FCFA, OFFER_URL


def test_constants():
    assert OFFER_PRICE_FCFA == 29000 and OFFER_URL == "https://wooplans.com/catalogue-premium"
    assert len(FORBIDDEN_ZERNIO_ACCOUNTS) == 3
