from decimal import Decimal

import pytest

from backend.app.domain.enums import (
    RecoveryStrategy,
)
from backend.app.services.decision_engine import (
    StrategyDecision,
)
from backend.app.services.recovery_decision_explanation import (
    RecoveryDecisionExplanationService,
)


@pytest.fixture
def service():
    return RecoveryDecisionExplanationService()


def create_decision(
    *,
    strategy=RecoveryStrategy.RETRY_PAYMENT,
    probability=0.85,
    revenue=Decimal("850.00"),
    score=0.85,
):
    return StrategyDecision(
        strategy=strategy,
        predicted_probability=probability,
        predicted_revenue=revenue,
        decision_score=score,
        reason="Test recovery decision.",
    )


@pytest.mark.parametrize(
    (
        "probability",
        "expected",
    ),
    [
        (0.90, "high"),
        (0.80, "high"),
        (0.79, "medium"),
        (0.50, "medium"),
        (0.49, "low"),
        (0.10, "low"),
    ],
)
def test_confidence_labels(
    service,
    probability,
    expected,
):
    assert (
        service._confidence(
            probability,
        )
        == expected
    )


@pytest.mark.parametrize(
    (
        "score",
        "expected",
    ),
    [
        (0.90, "high"),
        (0.80, "high"),
        (0.79, "medium"),
        (0.50, "medium"),
        (0.49, "low"),
        (0.10, "low"),
    ],
)
def test_priority_labels(
    service,
    score,
    expected,
):
    assert (
        service._priority(
            score,
        )
        == expected
    )


def test_explain_preserves_strategy(
    service,
):
    decision = create_decision(
        strategy=RecoveryStrategy.RECOVERY_LINK,
    )

    result = service.explain(
        decision,
    )

    assert (
        result.strategy
        == RecoveryStrategy.RECOVERY_LINK
    )


def test_explain_preserves_probability(
    service,
):
    decision = create_decision(
        probability=0.72,
    )

    result = service.explain(
        decision,
    )

    assert result.confidence == 0.72


def test_explain_preserves_expected_revenue(
    service,
):
    decision = create_decision(
        revenue=Decimal("720.00"),
    )

    result = service.explain(
        decision,
    )

    assert (
        result.expected_revenue
        == Decimal("720.00")
    )


def test_high_confidence_high_priority_decision(
    service,
):
    decision = create_decision(
        probability=0.90,
        score=0.95,
    )

    result = service.explain(
        decision,
    )

    assert result.priority == "high"

    assert (
        "high recovery confidence"
        in result.explanation
    )

    assert (
        "high execution priority"
        in result.explanation
    )


def test_medium_confidence_decision(
    service,
):
    decision = create_decision(
        probability=0.65,
        score=0.65,
    )

    result = service.explain(
        decision,
    )

    assert (
        "medium recovery confidence"
        in result.explanation
    )

    assert result.priority == "medium"


def test_low_confidence_decision(
    service,
):
    decision = create_decision(
        probability=0.30,
        score=0.30,
    )

    result = service.explain(
        decision,
    )

    assert (
        "low recovery confidence"
        in result.explanation
    )

    assert result.priority == "low"


def test_signals_include_strategy(
    service,
):
    decision = create_decision(
        strategy=RecoveryStrategy.SEND_REMINDER,
    )

    result = service.explain(
        decision,
    )

    assert (
        "strategy:send_reminder"
        in result.signals
    )


def test_signals_include_probability_and_score(
    service,
):
    decision = create_decision(
        probability=0.75,
        score=0.8123,
    )

    result = service.explain(
        decision,
    )

    assert (
        "probability:0.75"
        in result.signals
    )

    assert (
        "decision_score:0.8123"
        in result.signals
    )


def test_positive_revenue_signal_is_added(
    service,
):
    decision = create_decision(
        revenue=Decimal("100.00"),
    )

    result = service.explain(
        decision,
    )

    assert (
        "positive_expected_revenue"
        in result.signals
    )


def test_zero_revenue_does_not_add_positive_signal(
    service,
):
    decision = create_decision(
        revenue=Decimal("0"),
    )

    result = service.explain(
        decision,
    )

    assert (
        "positive_expected_revenue"
        not in result.signals
    )


def test_reason_is_included_in_explanation(
    service,
):
    decision = StrategyDecision(
        strategy=RecoveryStrategy.ESCALATE,
        predicted_probability=0.60,
        predicted_revenue=Decimal("600.00"),
        decision_score=0.60,
        reason="Human review is recommended.",
    )

    result = service.explain(
        decision,
    )

    assert (
        "Human review is recommended."
        in result.explanation
    )