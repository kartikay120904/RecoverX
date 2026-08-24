from uuid import UUID, uuid5
from backend.app.domain.models import Merchant


MERCHANT_NAMES = [
    "NovaMart",
    "UrbanCart",
    "QuickBasket",
    "TechNest",
    "DailyNeeds",
]
SIMULATION_NAMESPACE = UUID(
    "12345678-1234-5678-1234-567812345678"
)


def generate_merchants(count: int) -> list[Merchant]:
    if count <= 0:
        raise ValueError("Merchant count must be greater than zero.")

    merchants: list[Merchant] = []

    for index in range(count):
        name = MERCHANT_NAMES[index % len(MERCHANT_NAMES)]

        merchants.append(
    Merchant(
        merchant_id=uuid5(
            SIMULATION_NAMESPACE,
            f"merchant-{index}",
        ),
        name=f"{name}-{index + 1}",
        currency="INR",
    )
)

    return merchants