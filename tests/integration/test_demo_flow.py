import pytest

pytestmark = pytest.mark.integration


def seed_nested_users(client, payload):
    response = client.put("/.json", json=payload)
    assert response.status_code == 200
    assert response.json() == payload


def test_original_university_demo_runs_end_to_end_on_v2(client, nested_users_payload):
    api_paths = client.app.openapi()["paths"]
    assert {"/.json", "/{path}.json", "/set-index"} <= api_paths.keys()
    assert "/api/v1/set-index" not in api_paths
    for path in ("/.json", "/{path}.json"):
        assert all("_v2_" in operation["operationId"] for operation in api_paths[path].values())

    # The presentation started with existing data and a preconfigured sample collection.
    assert client.put("/nested-users.json", json={"stale": {"value": True}}).status_code == 200
    sample_values = {"first": "alpha", "second": "sigma", "third": "zeta"}
    assert client.put("/sample-dummy.json", json=sample_values).status_code == 200
    assert (
        client.put(
            "/set-index",
            params={"path": "sample-dummy"},
            json=".value",
        ).status_code
        == 200
    )

    # 1. Delete old nested-users data.
    response = client.delete("/nested-users.json")
    assert response.status_code == 200
    assert response.json() is None

    # 2-3. Insert and retrieve the presentation fixture.
    seed_nested_users(client, nested_users_payload)
    assert client.get("/nested-users.json").json() == nested_users_payload["nested-users"]

    # 4. Add the exact dummy user from the presentation.
    mia = {
        "userId": 7423,
        "name": {"first": "Mia", "last": "Brownlee"},
        "contact": {
            "phoneNumber": "9876354321",
            "emailAddress": "mia.brown@learningcontainer.com",
        },
        "age": 21,
    }
    response = client.post("/nested-users.json", json=mia)
    assert response.status_code == 200
    mia_id = response.json()["name"]
    assert client.get(f"/nested-users/{mia_id}.json").json() == mia

    # 5. Apply the three updates in their original order.
    assert client.put("/nested-users/698/age.json", json=144).json() == 144
    assert client.patch("/nested-users/698.json", json={"age": 34, "name/last": "Daviz"}).json() == {
        "age": 34,
        "name/last": "Daviz",
    }
    assert client.patch(
        "/nested-users.json",
        json={"698/contact/phoneNumber": "6784563213", "512/age": 35},
    ).json() == {"698/contact/phoneNumber": "6784563213", "512/age": 35}

    # 6. Force-create and then remove the extra field.
    assert client.put("/nested-users/512/extra.json", json=True).json() is True
    assert client.delete("/nested-users/512/extra.json").status_code == 200
    assert "extra" not in client.get("/nested-users/512.json").json()

    # 7. Query the accumulated presentation state.
    all_users = client.get("/nested-users.json").json()
    assert all_users[mia_id] == mia
    assert all_users["698"]["age"] == 34
    assert all_users["698"]["name"]["last"] == "Daviz"
    assert all_users["698"]["contact"]["phoneNumber"] == "6784563213"
    assert all_users["512"]["age"] == 35

    response = client.put(
        "/set-index",
        params={"path": "nested-users"},
        json=[".value", "age", "name/first"],
    )
    assert response.status_code == 200

    response = client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "limitToFirst": 2},
    )
    assert [user["name"]["first"] for user in response.json().values()] == ["Ava", "Darshan"]

    response = client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "startAt": '"M"', "endAt": '"T"'},
    )
    assert [user["name"]["first"] for user in response.json().values()] == [
        "Mia",
        "Noah",
        "Oliver",
        "Parsimon",
        "Sophia",
    ]

    response = client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "equalTo": '"Noah"'},
    )
    assert list(response.json()) == ["315"]

    response = client.get(
        "/sample-dummy.json",
        params={"orderBy": '"$value"', "limitToLast": 2, "startAt": '"s"'},
    )
    assert response.json() == {"third": "zeta", "second": "sigma"}


def test_v2_root_put_and_get(client, nested_users_payload):
    seed_nested_users(client, nested_users_payload)

    response = client.get("/nested-users.json")

    assert response.status_code == 200
    assert response.json() == nested_users_payload["nested-users"]


def test_demo_reset_deletes_nested_users_collection(client, nested_users_payload):
    seed_nested_users(client, nested_users_payload)

    response = client.delete("/nested-users.json")

    assert response.status_code == 200
    assert response.json() is None
    assert client.get("/nested-users.json").json() == {}


def test_v2_nested_crud_matches_demo_flow(client, nested_users_payload):
    seed_nested_users(client, nested_users_payload)

    response = client.post(
        "/nested-users.json",
        json={"userId": 7423, "name": {"first": "Mia", "last": "Brownlee"}, "age": 21},
    )
    assert response.status_code == 200
    generated_id = response.json()["name"]
    assert client.get(f"/nested-users/{generated_id}.json").json()["userId"] == 7423

    assert client.put("/nested-users/698/age.json", json=144).json() == 144
    assert client.patch("/nested-users/698.json", json={"age": 34, "name/last": "Daviz"}).status_code == 200
    assert (
        client.patch(
            "/nested-users.json",
            json={"698/contact/phoneNumber": "6784563213", "512/age": 35},
        ).status_code
        == 200
    )

    user_698 = client.get("/nested-users/698.json").json()
    assert user_698["age"] == 34
    assert user_698["name"]["last"] == "Daviz"
    assert user_698["contact"]["phoneNumber"] == "6784563213"
    assert client.get("/nested-users/512/age.json").json() == 35

    assert client.put("/nested-users/512/extra.json", json=True).status_code == 200
    assert client.delete("/nested-users/512/extra.json").status_code == 200
    assert "extra" not in client.get("/nested-users/512.json").json()


def test_v2_indexes_and_queries_match_demo_flow(client, nested_users_payload):
    seed_nested_users(client, nested_users_payload)

    response = client.put(
        "/set-index",
        params={"path": "nested-users"},
        json=[".value", "age", "name/first"],
    )
    assert response.status_code == 200

    response = client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "limitToFirst": 2},
    )
    assert response.status_code == 200
    assert [user["name"]["first"] for user in response.json().values()] == ["Ava", "Darshan"]

    response = client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "equalTo": '"Noah"'},
    )
    assert response.status_code == 200
    assert list(response.json()) == ["315"]

    response = client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "startAt": '"M"', "endAt": '"T"'},
    )
    assert response.status_code == 200
    assert [user["name"]["first"] for user in response.json().values()] == [
        "Noah",
        "Oliver",
        "Parsimon",
        "Sophia",
    ]

    assert client.get("/get-rules").json()["nested-users"] == [".value", "age", "name/first"]
    assert client.delete("/delete-index", params={"path": "nested-users"}).status_code == 200


def test_v2_validation_errors_are_deterministic(client, nested_users_payload):
    assert client.put("/scalar.json", json=42).status_code == 422

    seed_nested_users(client, nested_users_payload)
    response = client.get("/nested-users.json", params={"limitToFirst": 2})

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "orderBy must be defined when other query parameters are defined"
