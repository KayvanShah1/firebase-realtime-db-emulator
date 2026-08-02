import pytest
from pymongo.errors import ServerSelectionTimeoutError

pytestmark = pytest.mark.integration


def test_health_check_reports_database_readiness(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy", "database": "connected"}


def test_health_check_reports_database_failure(client, monkeypatch):
    class UnavailableDatabase:
        async def command(self, command: str):
            raise ServerSelectionTimeoutError(f"Cannot run {command}")

    monkeypatch.setattr("app.api.health.get_database", lambda: UnavailableDatabase())

    response = client.get("/health")

    assert response.status_code == 503
    assert response.json() == {"detail": {"status": "unhealthy", "database": "unavailable"}}
