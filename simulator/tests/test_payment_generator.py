from simulator.data.payment_generator import (
    PaymentBatchGenerator,
)

from backend.app.domain.enums import (
    PaymentStatus,
)


def test_generator_creates_requested_count():

    payments = (
        PaymentBatchGenerator(
            seed=42,
        ).generate(
            count=50,
        )
    )

    assert len(
        payments
    ) == 50


def test_generated_payments_are_failed():

    payments = (
        PaymentBatchGenerator(
            seed=42,
        ).generate(
            count=20,
        )
    )

    assert all(
        payment.status
        == PaymentStatus.FAILED
        for payment in payments
    )


def test_generated_payments_have_failure_codes():

    payments = (
        PaymentBatchGenerator(
            seed=42,
        ).generate(
            count=20,
        )
    )

    assert all(
        payment.failure_code
        is not None
        for payment in payments
    )


def test_generator_creates_escalation_cases():

    payments = (
        PaymentBatchGenerator(
            seed=42,
        ).generate(
            count=20,
        )
    )

    escalation_candidates = [
        payment
        for payment in payments
        if payment.attempt_number >= 4
    ]

    assert len(
        escalation_candidates
    ) >= 2


def test_generator_is_deterministic():

    first = (
        PaymentBatchGenerator(
            seed=42,
        ).generate(
            count=20,
        )
    )

    second = (
        PaymentBatchGenerator(
            seed=42,
        ).generate(
            count=20,
        )
    )

    assert [
        payment.payment_id
        for payment in first
    ] == [
        payment.payment_id
        for payment in second
    ]

    assert [
        payment.amount
        for payment in first
    ] == [
        payment.amount
        for payment in second
    ]

    assert [
        payment.failure_code
        for payment in first
    ] == [
        payment.failure_code
        for payment in second
    ]

    assert [
        payment.attempt_number
        for payment in first
    ] == [
        payment.attempt_number
        for payment in second
    ]


def test_generator_rejects_invalid_count():

    generator = (
        PaymentBatchGenerator()
    )

    try:

        generator.generate(
            count=0,
        )

        assert False

    except ValueError:

        assert True