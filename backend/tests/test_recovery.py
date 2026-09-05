from uuid import UUID

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


# =========================================================
# Helper
# =========================================================

def get_recommendations() -> list[dict]:
    """
    Fetch the current recovery recommendations.

    The API should always return a JSON list.
    """

    response = client.get(
        "/recovery/recommendations"
    )

    assert response.status_code == 200, (
        response.text
    )

    recommendations = response.json()

    assert isinstance(
        recommendations,
        list,
    )

    assert len(
        recommendations
    ) > 0

    return recommendations


def get_recommended_payment_id() -> str:
    """
    Return a payment ID that currently has a proposed
    recovery recommendation.
    """

    recommendations = get_recommendations()

    payment_id = recommendations[0].get(
        "payment_id"
    )

    assert payment_id is not None

    return payment_id


# =========================================================
# GET /recovery/recommendations
# =========================================================

def test_get_recommendations():

    response = client.get(
        "/recovery/recommendations"
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert isinstance(
        data,
        list,
    )

    assert len(data) > 0

    recommendation = data[0]

    assert (
        "payment_id"
        in recommendation
    )

    assert (
        "status"
        in recommendation
    )

    assert (
        "strategy"
        in recommendation
    )


# =========================================================
# GET /recovery/{payment_id}
# =========================================================

def test_get_single_recovery():

    recommendations = get_recommendations()

    payment_id = recommendations[0][
        "payment_id"
    ]

    response = client.get(
        f"/recovery/{payment_id}"
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    # Important regression protection:
    # the endpoint must never return JSON null.
    assert data is not None

    assert isinstance(
        data,
        dict,
    )

    assert (
        data["payment_id"]
        == payment_id
    )

    assert (
        "status"
        in data
    )

    assert (
        "strategy"
        in data
    )


# =========================================================
# POST /recovery/{payment_id}/approve
# =========================================================

def test_approve_recovery():

    payment_id = (
        get_recommended_payment_id()
    )

    response = client.post(
        f"/recovery/{payment_id}/approve"
    )

    assert response.status_code == 200, (
        response.text
    )

    data = response.json()

    assert data is not None

    assert isinstance(
        data,
        dict,
    )

    assert (
        data["payment_id"]
        == payment_id
    )

    assert (
        data["status"]
        == "approved"
    )


# =========================================================
# POST /recovery/{payment_id}/execute
#
# Execution without approval must fail.
# =========================================================

def test_execute_requires_approval():

    recommendations = get_recommendations()

    payment_id = recommendations[0][
        "payment_id"
    ]

    response = client.post(
        f"/recovery/{payment_id}/execute"
    )

    # The API should reject execution when approval
    # has not happened first.
    assert response.status_code in (
        400,
        409,
    ), response.text

    data = response.json()

    assert (
        "detail"
        in data
    )


# =========================================================
# Approve -> Execute
#
# This is the most important state transition test.
# =========================================================

def test_approve_then_execute():

    payment_id = (
        get_recommended_payment_id()
    )

    # -----------------------------------------------------
    # Approve
    # -----------------------------------------------------

    approve_response = client.post(
        f"/recovery/{payment_id}/approve"
    )

    assert (
        approve_response.status_code
        == 200
    ), approve_response.text

    approved_data = (
        approve_response.json()
    )

    assert (
        approved_data["payment_id"]
        == payment_id
    )

    assert (
        approved_data["status"]
        == "approved"
    )

    # -----------------------------------------------------
    # Verify approval persisted
    # -----------------------------------------------------

    recovery_response = client.get(
        f"/recovery/{payment_id}"
    )

    assert (
        recovery_response.status_code
        == 200
    ), recovery_response.text

    recovery_data = (
        recovery_response.json()
    )

    assert (
        recovery_data is not None
    )

    assert (
        recovery_data["status"]
        == "approved"
    )

    # -----------------------------------------------------
    # Execute
    # -----------------------------------------------------

    execute_response = client.post(
        f"/recovery/{payment_id}/execute"
    )

    # The recovery engine may schedule execution for a
    # future time. Both outcomes are valid here:
    #
    # 200 -> executed successfully
    # 409 -> approved but not due yet

    assert (
        execute_response.status_code
        in (
            200,
            409,
        )
    ), execute_response.text

    response_data = (
        execute_response.json()
    )

    # -----------------------------------------------------
    # If executed immediately
    # -----------------------------------------------------

    if (
        execute_response.status_code
        == 200
    ):

        assert (
            response_data is not None
        )

        assert isinstance(
            response_data,
            dict,
        )

        assert (
            response_data["payment_id"]
            == payment_id
        )

    # -----------------------------------------------------
    # If scheduled for future execution
    # -----------------------------------------------------

    if (
        execute_response.status_code
        == 409
    ):

        assert (
            "detail"
            in response_data
        )

        detail = response_data[
            "detail"
        ]

        assert isinstance(
            detail,
            dict,
        )

        assert (
            "scheduled_at"
            in detail
        )

        assert (
            detail["message"]
            == "Recovery execution is not due yet."
        )


# =========================================================
# Invalid payment
# =========================================================

def test_invalid_payment_returns_404():

    fake_payment_id = UUID(
        "00000000-0000-0000-0000-000000000001"
    )

    response = client.get(
        f"/recovery/{fake_payment_id}"
    )

    assert (
        response.status_code
        == 404
    ), response.text

    data = response.json()

    assert (
        "detail"
        in data
    )


# =========================================================
# Additional regression test
#
# Invalid approval must return 404.
# =========================================================

def test_invalid_payment_approval_returns_404():

    fake_payment_id = UUID(
        "00000000-0000-0000-0000-000000000002"
    )

    response = client.post(
        f"/recovery/{fake_payment_id}/approve"
    )

    assert (
        response.status_code
        == 404
    ), response.text


# =========================================================
# Additional regression test
#
# Invalid execution must return 404.
# =========================================================

def test_invalid_payment_execution_returns_404():

    fake_payment_id = UUID(
        "00000000-0000-0000-0000-000000000003"
    )

    response = client.post(
        f"/recovery/{fake_payment_id}/execute"
    )

    assert (
        response.status_code
        == 404
    ), response.text