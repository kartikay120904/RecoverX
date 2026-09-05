from fastapi.testclient import TestClient

from backend.app.api.main import app

client = TestClient(app)

def _get_failed_payment_id() -> str:
    response = client.get(
        "/recovery/payments"
    )

    assert response.status_code == 200

    payments = response.json()["payments"]

    failed_payment = next(
        payment
        for payment in payments
        if payment["failure_code"] is not None
    )

    return failed_payment["payment_id"]


def test_recovery_execution_creates_audit_record():
    payment_id = _get_failed_payment_id()

    response = client.post(
        "/recovery/execute",
        json={
            "payment_id": payment_id,
            "action": "retry",
            "idempotency_key": (
                "audit-record-test-key-001"
            ),
        },
    )

    assert response.status_code in (
        200,
        201,
    )

    execution = response.json()

    execution_id = execution["execution_id"]

    history_response = client.get(
        f"/recovery/executions/{execution_id}"
    )

    assert history_response.status_code == 200

    history_execution = (
        history_response.json()
    )

    assert (
        history_execution["execution_id"]
        == execution_id
    )

    assert (
        history_execution["payment_id"]
        == payment_id
    )

    assert (
        history_execution["action"]
        == "retry"
    )


def test_idempotent_request_does_not_create_duplicate_audit_record():
    payment_id = _get_failed_payment_id()

    payload = {
        "payment_id": payment_id,
        "action": "retry",
        "idempotency_key": (
            "audit-idempotency-test-key-001"
        ),
    }

    first_response = client.post(
        "/recovery/execute",
        json=payload,
    )

    second_response = client.post(
        "/recovery/execute",
        json=payload,
    )

    assert first_response.status_code in (
        200,
        201,
    )

    assert second_response.status_code in (
        200,
        201,
    )

    first_execution = (
        first_response.json()
    )

    second_execution = (
        second_response.json()
    )

    assert (
        first_execution["execution_id"]
        ==
        second_execution["execution_id"]
    )


def test_recovery_execution_history_returns_records():
    payment_id = _get_failed_payment_id()

    response = client.post(
        "/recovery/execute",
        json={
            "payment_id": payment_id,
            "action": "manual_review",
            "idempotency_key": (
                "audit-history-test-key-001"
            ),
        },
    )

    assert response.status_code in (
        200,
        201,
    )

    history_response = client.get(
        "/recovery/executions"
    )

    assert history_response.status_code == 200

    executions = history_response.json()

    assert isinstance(
        executions,
        list,
    )

    assert any(
        execution["payment_id"]
        == payment_id
        for execution
        in executions
    )


def test_payment_execution_history_returns_matching_records():
    payment_id = _get_failed_payment_id()

    response = client.post(
        "/recovery/execute",
        json={
            "payment_id": payment_id,
            "action": "cancel",
            "idempotency_key": (
                "payment-history-test-key-001"
            ),
        },
    )

    assert response.status_code in (
        200,
        201,
    )

    history_response = client.get(
        f"/recovery/{payment_id}/executions"
    )

    assert history_response.status_code == 200

    executions = history_response.json()

    assert isinstance(
        executions,
        list,
    )

    assert len(executions) >= 1

    assert all(
        execution["payment_id"]
        == payment_id
        for execution
        in executions
    )