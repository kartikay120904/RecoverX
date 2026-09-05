from decimal import Decimal

from integrations.recovery.outcome_store import (
    RecoveryOutcomeStore,
    StoredRecoveryOutcome,
)


def test_store_records_completed_recovery():
    store = RecoveryOutcomeStore()

    outcome = StoredRecoveryOutcome(
        payment_link_id="plink_test_123",
        razorpay_payment_id="pay_test_123",
        recovered_amount=Decimal("500.00"),
        currency="INR",
    )

    stored = store.record(
        outcome
    )

    assert stored == outcome

    assert store.count() == 1

    assert (
        store.get(
            "plink_test_123"
        )
        == outcome
    )


def test_store_prevents_duplicate_webhook_records():
    store = RecoveryOutcomeStore()

    first = StoredRecoveryOutcome(
        payment_link_id="plink_test_duplicate",
        razorpay_payment_id="pay_first",
        recovered_amount=Decimal("250.00"),
        currency="INR",
    )

    duplicate = StoredRecoveryOutcome(
        payment_link_id="plink_test_duplicate",
        razorpay_payment_id="pay_second",
        recovered_amount=Decimal("999.00"),
        currency="INR",
    )

    stored_first = store.record(
        first
    )

    stored_duplicate = store.record(
        duplicate
    )

    assert stored_first == first

    assert stored_duplicate == first

    assert store.count() == 1

    assert (
        store.total_recovered_amount()
        == Decimal("250.00")
    )


def test_store_calculates_total_recovered_amount():
    store = RecoveryOutcomeStore()

    store.record(
        StoredRecoveryOutcome(
            payment_link_id="plink_1",
            razorpay_payment_id="pay_1",
            recovered_amount=Decimal("100.00"),
            currency="INR",
        )
    )

    store.record(
        StoredRecoveryOutcome(
            payment_link_id="plink_2",
            razorpay_payment_id="pay_2",
            recovered_amount=Decimal("250.00"),
            currency="INR",
        )
    )

    store.record(
        StoredRecoveryOutcome(
            payment_link_id="plink_usd",
            razorpay_payment_id="pay_usd",
            recovered_amount=Decimal("50.00"),
            currency="USD",
        )
    )

    assert (
        store.count()
        == 3
    )

    assert (
        store.total_recovered_amount(
            "INR"
        )
        == Decimal("350.00")
    )

    assert (
        store.total_recovered_amount(
            "USD"
        )
        == Decimal("50.00")
    )


def test_empty_store_has_zero_recovered_amount():
    store = RecoveryOutcomeStore()

    assert store.count() == 0

    assert (
        store.total_recovered_amount()
        == Decimal("0")
    )

    assert store.all() == []