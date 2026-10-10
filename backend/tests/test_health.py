from rest_framework.test import APIClient


def test_health_check_returns_ok() -> None:
    response = APIClient().get("/api/v1/health/")

    assert response.status_code == 200
    assert response.json() == {"data": {"status": "ok"}}