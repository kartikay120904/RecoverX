from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_recovery_execution_is_idempotent():
    response = client.get("/recovery/payments")

    assert response.status_code == 200

    payments = response.json()["payments"]

    failed_payment = next(
        payment
        for payment in payments
        if payment["failure_code"] is not None
    )

    payment_id = failed_payment["payment_id"]

    payload = {
        "payment_id": payment_id,
        "action": "retry",
        "idempotency_key": "test-recovery-idempotency-key-001",
    }

    first_response = client.post(
        "/recovery/execute",
        json=payload,
    )

    assert first_response.status_code in (200, 201)

    second_response = client.post(
        "/recovery/execute",
        json=payload,
    )

    assert second_response.status_code in (200, 201)

    first_data = first_response.json()
    second_data = second_response.json()

    assert first_data == second_data


def test_different_idempotency_keys_create_independent_requests():
    response = client.get("/recovery/payments")

    assert response.status_code == 200

    payments = response.json()["payments"]

    failed_payment = next(
        payment
        for payment in payments
        if payment["failure_code"] is not None
    )

    payment_id = failed_payment["payment_id"]

    first_response = client.post(
        "/recovery/execute",
        json={
            "payment_id": payment_id,
            "action": "retry",
            "idempotency_key": "test-key-001",
        },
    )

    second_response = client.post(
        "/recovery/execute",
        json={
            "payment_id": payment_id,
            "action": "retry",
            "idempotency_key": "test-key-002",
        },
    )

    assert first_response.status_code in (200, 201)
    assert second_response.status_code in (200, 201)


def test_idempotency_key_with_different_payload_is_rejected():
    response = client.get("/recovery/payments")

    assert response.status_code == 200

    payments = response.json()["payments"]

    failed_payment = next(
        payment
        for payment in payments
        if payment["failure_code"] is not None
    )

    payment_id = failed_payment["payment_id"]

    idempotency_key = "test-conflicting-key-001"

    first_response = client.post(
        "/recovery/execute",
        json={
            "payment_id": payment_id,
            "action": "retry",
            "idempotency_key": idempotency_key,
        },
    )

    assert first_response.status_code in (200, 201)

    second_response = client.post(
        "/recovery/execute",
        json={
            "payment_id": payment_id,
            "action": "cancel",
            "idempotency_key": idempotency_key,
        },
    )

    assert second_response.status_code in (400, 409, 422)