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


def test_v1_deep_paths_use_the_legacy_document_adapter(client):
    users = {"users": {"1": {"profile": {"name": "Ada"}}}}
    assert client.put("/api/v1/.json", json=users).status_code == 200

    assert client.put("/api/v1/users/1/profile/email.json", json="ada@example.com").status_code == 200
    response = client.post("/api/v1/users/1/messages.json", json={"text": "hello"})
    message_id = response.json()["name"]
    assert (
        client.patch(
            "/api/v1/users/1/profile.json",
            json={"name": "Grace", "contact/phone": "1234"},
        ).status_code
        == 200
    )

    assert client.get("/api/v1/users/1.json").json() == {
        "profile": {
            "name": "Grace",
            "email": "ada@example.com",
            "contact": {"phone": "1234"},
        },
        "messages": {message_id: {"text": "hello"}},
    }


def test_v1_preserves_legacy_validation_and_missing_key_responses(client):
    assert client.put("/api/v1/.json").status_code == 400
    assert client.get("/api/v1/users.json", params={"startAt": '"a"'}).status_code == 400
    assert client.delete("/api/v1/missing.json").status_code == 404
