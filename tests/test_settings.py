from wooplans.settings import FORBIDDEN_ZERNIO_ACCOUNTS, OFFER_PRICE_FCFA, OFFER_URL


def test_constants():
    assert OFFER_PRICE_FCFA == 39000 and OFFER_URL.endswith("/digital")
    assert len(FORBIDDEN_ZERNIO_ACCOUNTS) == 3
