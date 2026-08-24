from dataclasses import dataclass


@dataclass(frozen=True)
class PaymentSimulationConfig:
    seed: int = 42

    # Baseline synthetic success rates.
    # These are simulation parameters, not Razorpay production statistics.
    success_rates: dict[str, float] | None = None

    def get_success_rates(self) -> dict[str, float]:
        if self.success_rates is not None:
            return self.success_rates.copy()

        return {
            "upi": 0.92,
            "card": 0.94,
            "netbanking": 0.90,
            "wallet": 0.93,
        }