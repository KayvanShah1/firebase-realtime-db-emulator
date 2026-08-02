import pytest

pytestmark = pytest.mark.real_db


def test_health_and_original_demo_flow_against_real_mongodb(
    real_db_client,
    nested_users_payload,
):
    health_response = real_db_client.get("/health")
    assert health_response.status_code == 200
    assert health_response.json() == {"status": "healthy", "database": "connected"}

    # Reproduce the setup and reset at the beginning of the original demo.
    assert real_db_client.put("/nested-users.json", json={"stale": {"value": True}}).status_code == 200
    sample_values = {"first": "alpha", "second": "sigma", "third": "zeta"}
    assert real_db_client.put("/sample-dummy.json", json=sample_values).status_code == 200
    assert (
        real_db_client.put(
            "/set-index",
            params={"path": "sample-dummy"},
            json=".value",
        ).status_code
        == 200
    )
    assert real_db_client.delete("/nested-users.json").status_code == 200

    # Seed, read, and append the exact presentation data through the v2 API.
    put_response = real_db_client.put("/.json", json=nested_users_payload)
    assert put_response.status_code == 200
    assert put_response.json() == nested_users_payload
    assert real_db_client.get("/nested-users.json").json() == nested_users_payload["nested-users"]

    mia = {
        "userId": 7423,
        "name": {"first": "Mia", "last": "Brownlee"},
        "contact": {
            "phoneNumber": "9876354321",
            "emailAddress": "mia.brown@learningcontainer.com",
        },
        "age": 21,
    }
    post_response = real_db_client.post("/nested-users.json", json=mia)
    assert post_response.status_code == 200
    mia_id = post_response.json()["name"]
    assert real_db_client.get(f"/nested-users/{mia_id}.json").json() == mia

    # Exercise every nested mutation shape from the presentation.
    assert real_db_client.put("/nested-users/698/age.json", json=144).json() == 144
    assert real_db_client.patch(
        "/nested-users/698.json",
        json={"age": 34, "name/last": "Daviz"},
    ).json() == {"age": 34, "name/last": "Daviz"}
    assert real_db_client.patch(
        "/nested-users.json",
        json={"698/contact/phoneNumber": "6784563213", "512/age": 35},
    ).json() == {"698/contact/phoneNumber": "6784563213", "512/age": 35}
    assert real_db_client.put("/nested-users/512/extra.json", json=True).json() is True
    assert real_db_client.delete("/nested-users/512/extra.json").status_code == 200

    all_users = real_db_client.get("/nested-users.json").json()
    assert all_users[mia_id] == mia
    assert all_users["698"]["age"] == 34
    assert all_users["698"]["name"]["last"] == "Daviz"
    assert all_users["698"]["contact"]["phoneNumber"] == "6784563213"
    assert all_users["512"]["age"] == 35
    assert "extra" not in all_users["512"]

    # Verify the original indexed query sequence against real MongoDB semantics.
    index_response = real_db_client.put(
        "/set-index",
        params={"path": "nested-users"},
        json=[".value", "age", "name/first"],
    )
    assert index_response.status_code == 200

    first_two_response = real_db_client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "limitToFirst": 2},
    )
    assert [user["name"]["first"] for user in first_two_response.json().values()] == ["Ava", "Darshan"]

    range_response = real_db_client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "startAt": '"M"', "endAt": '"T"'},
    )
    assert [user["name"]["first"] for user in range_response.json().values()] == [
        "Mia",
        "Noah",
        "Oliver",
        "Parsimon",
        "Sophia",
    ]

    equal_response = real_db_client.get(
        "/nested-users.json",
        params={"orderBy": '"name/first"', "equalTo": '"Noah"'},
    )
    assert list(equal_response.json()) == ["315"]

    value_response = real_db_client.get(
        "/sample-dummy.json",
        params={"orderBy": '"$value"', "limitToLast": 2, "startAt": '"s"'},
    )
    assert value_response.json() == {"third": "zeta", "second": "sigma"}
