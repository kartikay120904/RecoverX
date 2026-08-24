from simulator.generators.merchant import generate_merchants


def test_generate_merchants():
    merchants = generate_merchants(5)

    assert len(merchants) == 5

    assert all(
        merchant.currency == "INR"
        for merchant in merchants
    )


def test_generate_merchants_rejects_invalid_count():
    try:
        generate_merchants(0)
        assert False
    except ValueError:
        assert True