import pytest

pytestmark = pytest.mark.integration


def test_v1_root_put_and_nested_get(client, sample_data_payload):
    response = client.put("/api/v1/.json", json=sample_data_payload)

    assert response.status_code == 200
    assert response.json() == sample_data_payload

    response = client.get("/api/v1/users.json")

    assert response.status_code == 200
    assert response.json() == sample_data_payload["users"]


def test_v1_nested_crud(client):
    users = {"users": {"1": {"name": "Ada", "active": True}}}
    assert client.put("/api/v1/.json", json=users).status_code == 200

    response = client.patch("/api/v1/users/1.json", json={"active": False})
    assert response.status_code == 200
    assert response.json() == {"active": False}
    assert client.get("/api/v1/users/1.json").json() == {"name": "Ada", "active": False}

    response = client.delete("/api/v1/users/1/active.json")
    assert response.status_code == 200
    assert client.get("/api/v1/users/1.json").json() == {"name": "Ada"}
