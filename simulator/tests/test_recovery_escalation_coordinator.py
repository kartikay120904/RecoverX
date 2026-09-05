from dataclasses import dataclass
from decimal import Decimal
from random import Random

from backend.app.domain.enums import (
    PaymentFailureCode,
    PaymentMethod,
)
from backend.app.domain.models import (
    Payment,
    RecoveryAttempt,
)

from backend.app.recovery.escalation_adapter import (
    RecoveryEscalationAdapterResult,
)

from backend.app.recovery.orchestrator import (
    RecoveryOrchestrationResult,
)

from backend.app.recovery.recovery_escalation_coordinator import (
    RecoveryEscalationCoordinator,
)


def create_payment() -> Payment:
    return Payment(
        amount=Decimal("1000"),
        method=PaymentMethod.UPI,
        failure_code=PaymentFailureCode.BANK_TIMEOUT,
    )


@dataclass
class FakeOrchestrator:
    result: RecoveryOrchestrationResult

    def recover(
        self,
        *,
        payment: Payment,
        rng: Random,
    ) -> RecoveryOrchestrationResult:
        return self.result


@dataclass
class FakeEscalationAdapter:
    result: RecoveryEscalationAdapterResult

    received_payment: Payment | None = None
    received_orchestration: (
        RecoveryOrchestrationResult | None
    ) = None

    def evaluate(
        self,
        *,
        payment: Payment,
        orchestration: RecoveryOrchestrationResult,
    ) -> RecoveryEscalationAdapterResult:

        self.received_payment = payment

        self.received_orchestration = (
            orchestration
        )

        return self.result


def create_orchestration_result(
    *,
    executed: bool = False,
    blocked: bool = False,
    requires_approval: bool = False,
    reason: str = "Recovery workflow completed.",
) -> RecoveryOrchestrationResult:

    return RecoveryOrchestrationResult(
        attempt=None,
        policy_decision=None,
        executed=executed,
        blocked=blocked,
        requires_approval=requires_approval,
        escalation_required=requires_approval,
        reason=reason,
    )


def test_coordinator_runs_recovery_without_adapter():

    orchestration = (
        create_orchestration_result(
            executed=True,
        )
    )

    orchestrator = FakeOrchestrator(
        result=orchestration,
    )

    coordinator = (
        RecoveryEscalationCoordinator(
            orchestrator=orchestrator,
            escalation_adapter=None,
        )
    )

    payment = create_payment()

    result = coordinator.recover(
        payment=payment,
        rng=Random(42),
    )

    assert (
        result.orchestration
        is orchestration
    )

    assert result.escalation is None


def test_coordinator_passes_orchestration_to_adapter():

    orchestration = (
        create_orchestration_result(
            requires_approval=True,
            reason=(
                "Recovery requires human approval."
            ),
        )
    )

    adapter_result = (
        RecoveryEscalationAdapterResult(
            orchestration=orchestration,
            escalation=None,
        )
    )

    orchestrator = FakeOrchestrator(
        result=orchestration,
    )

    adapter = FakeEscalationAdapter(
        result=adapter_result,
    )

    coordinator = (
        RecoveryEscalationCoordinator(
            orchestrator=orchestrator,
            escalation_adapter=adapter,
        )
    )

    payment = create_payment()

    result = coordinator.recover(
        payment=payment,
        rng=Random(42),
    )

    assert (
        adapter.received_payment
        is payment
    )

    assert (
        adapter.received_orchestration
        is orchestration
    )

    assert (
        result.orchestration
        is orchestration
    )

    assert (
        result.escalation
        is adapter_result
    )


def test_successful_recovery_is_forwarded_to_adapter():

    orchestration = (
        create_orchestration_result(
            executed=True,
            blocked=False,
            requires_approval=False,
        )
    )

    adapter_result = (
        RecoveryEscalationAdapterResult(
            orchestration=orchestration,
            escalation=None,
        )
    )

    orchestrator = FakeOrchestrator(
        result=orchestration,
    )

    adapter = FakeEscalationAdapter(
        result=adapter_result,
    )

    coordinator = (
        RecoveryEscalationCoordinator(
            orchestrator=orchestrator,
            escalation_adapter=adapter,
        )
    )

    payment = create_payment()

    result = coordinator.recover(
        payment=payment,
        rng=Random(42),
    )

    assert (
        result.orchestration.executed
        is True
    )

    assert (
        result.escalation
        is adapter_result
    )

    assert (
        adapter.received_orchestration
        is orchestration
    )


def test_blocked_recovery_is_forwarded_to_adapter():

    orchestration = (
        create_orchestration_result(
            executed=False,
            blocked=True,
            requires_approval=False,
            reason=(
                "Recovery execution blocked."
            ),
        )
    )

    adapter_result = (
        RecoveryEscalationAdapterResult(
            orchestration=orchestration,
            escalation=None,
        )
    )

    orchestrator = FakeOrchestrator(
        result=orchestration,
    )

    adapter = FakeEscalationAdapter(
        result=adapter_result,
    )

    coordinator = (
        RecoveryEscalationCoordinator(
            orchestrator=orchestrator,
            escalation_adapter=adapter,
        )
    )

    payment = create_payment()

    result = coordinator.recover(
        payment=payment,
        rng=Random(42),
    )

    assert (
        result.orchestration.blocked
        is True
    )

    assert (
        adapter.received_orchestration
        is orchestration
    )

    assert (
        result.escalation
        is adapter_result
    )


def test_approval_recovery_is_forwarded_to_adapter():

    orchestration = (
        create_orchestration_result(
            executed=False,
            blocked=False,
            requires_approval=True,
            reason=(
                "Recovery requires human approval."
            ),
        )
    )

    adapter_result = (
        RecoveryEscalationAdapterResult(
            orchestration=orchestration,
            escalation=None,
        )
    )

    orchestrator = FakeOrchestrator(
        result=orchestration,
    )

    adapter = FakeEscalationAdapter(
        result=adapter_result,
    )

    coordinator = (
        RecoveryEscalationCoordinator(
            orchestrator=orchestrator,
            escalation_adapter=adapter,
        )
    )

    payment = create_payment()

    result = coordinator.recover(
        payment=payment,
        rng=Random(42),
    )

    assert (
        result.orchestration.requires_approval
        is True
    )

    assert (
        result.orchestration.escalation_required
        is True
    )

    assert (
        adapter.received_orchestration
        is orchestration
    )

    assert (
        result.escalation
        is adapter_result
    )