import hashlib
from random import Random
from uuid import UUID, uuid5
from backend.app.domain.models import Customer


SEGMENTS = [
    "new",
    "returning",
    "high_value",
    "low_value",
    "inactive",
]
SIMULATION_NAMESPACE = UUID(
    "12345678-1234-5678-1234-567812345678"
)

def hash_value(value: str) -> str:
    return hashlib.sha256(
        value.encode("utf-8")
    ).hexdigest()


def generate_customers(
    count: int,
    merchant_ids: list[UUID],
    rng: Random,
) -> list[Customer]:

    if count <= 0:
        raise ValueError("Customer count must be greater than zero.")

    if not merchant_ids:
        raise ValueError("At least one merchant is required.")

    customers: list[Customer] = []

    for index in range(count):
        merchant_id = rng.choice(merchant_ids)

        raw_email = f"customer{index}@example.com"
        raw_phone = f"+919000000{index:03d}"

        segment = rng.choices(
            SEGMENTS,
            weights=[25, 35, 15, 20, 5],
            k=1,
        )[0]

        customers.append(
            Customer(
    customer_id=uuid5(
        SIMULATION_NAMESPACE,
        f"customer-{index}",
    ),
    merchant_id=merchant_id,
                email_hash=hash_value(raw_email),
                phone_hash=hash_value(raw_phone),
                customer_segment=segment,
            )
        )

    return customers