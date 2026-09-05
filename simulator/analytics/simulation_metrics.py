from decimal import Decimal

from pydantic import BaseModel, Field


class SimulationMetrics(BaseModel):
    """
    Aggregated metrics for one RecoverX simulation run.
    """

    total_payments: int = Field(ge=0)

    failed_payments: int = Field(ge=0)

    recovery_candidates: int = Field(ge=0)

    recovery_attempts: int = Field(ge=0)

    successful_recoveries: int = Field(ge=0)

    failed_recoveries: int = Field(ge=0)

    revenue_at_risk: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    revenue_recovered: Decimal = Field(
        default=Decimal("0"),
        ge=0,
    )

    recovery_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
    )

    recovery_success_rate: float = Field(
        default=0.0,
        ge=0,
        le=100,
    )