from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal
from uuid import UUID


@dataclass(frozen=True)
class RecoveryExecutionRequest:
    """
    Immutable request passed to a recovery
    execution implementation.

    This abstraction prevents execution layers
    from depending directly on simulator internals.
    """

    payment_id: UUID

    recovery_id: UUID

    amount: Decimal

    currency: str = "INR"

    description: str | None = None


@dataclass(frozen=True)
class RecoveryExecutionResult:
    """
    Normalized result returned by every recovery
    execution implementation.

    Different execution providers can expose their
    own raw responses internally while RecoverX
    consumes this provider-independent result.
    """

    success: bool

    execution_id: str | None

    status: str

    recovery_url: str | None = None

    provider: str = "unknown"

    error: str | None = None


class RecoveryExecutionInterface(ABC):
    """
    Contract for executing a bounded recovery action.

    Implementations may execute through:

    - simulation
    - Razorpay
    - another payment provider

    The domain and orchestration layers should not
    depend directly on provider SDKs.
    """

    @abstractmethod
    def execute(
        self,
        *,
        request: RecoveryExecutionRequest,
    ) -> RecoveryExecutionResult:
        """
        Execute one bounded recovery action.
        """

        raise NotImplementedError