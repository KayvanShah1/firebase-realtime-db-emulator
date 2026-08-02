import pytest

pytestmark = pytest.mark.integration


@pytest.fixture
def ordered_records(client):
    records = {
        "a": {"name": "Ada", "score": 1, "tags": {"a": "alpha", "b": "beta", "c": "gamma"}},
        "b": {"name": "Grace", "score": 2},
        "c": {"name": "Linus", "score": 3},
    }
    assert client.put("/records.json", json=records).status_code == 200
    assert client.put("/set-index", params={"path": "records"}, json=["name", "score"]).status_code == 200
    return records


@pytest.mark.parametrize(
    ("query", "expected_keys"),
    [
        ({"limitToFirst": 2}, ["a", "b"]),
        ({"limitToLast": 2}, ["b", "c"]),
        ({"startAt": '"Grace"'}, ["b", "c"]),
        ({"endAt": '"Grace"'}, ["a", "b"]),
        ({"equalTo": '"Grace"'}, ["b"]),
        ({"startAt": '"Ada"', "endAt": '"Grace"'}, ["a", "b"]),
    ],
)
def test_child_ordering_contract(client, ordered_records, query, expected_keys):
    response = client.get("/records.json", params={"orderBy": '"name"', **query})

    assert response.status_code == 200
    assert list(response.json()) == expected_keys


@pytest.mark.parametrize(
    ("query", "expected_keys"),
    [
        ({"limitToFirst": 2}, ["a", "b"]),
        ({"limitToLast": 2}, ["b", "c"]),
        ({"startAt": '"b"'}, ["b", "c"]),
        ({"endAt": '"b"'}, ["a", "b"]),
        ({"equalTo": '"b"'}, ["b"]),
    ],
)
def test_key_ordering_contract(client, ordered_records, query, expected_keys):
    response = client.get("/records.json", params={"orderBy": '"$key"', **query})

    assert response.status_code == 200
    assert list(response.json()) == expected_keys


@pytest.mark.parametrize(
    ("query", "expected_keys"),
    [
        ({"limitToFirst": 2}, ["low", "mid"]),
        ({"limitToLast": 2}, ["mid", "high"]),
        ({"startAt": 2}, ["mid", "high"]),
        ({"endAt": 2}, ["low", "mid"]),
        ({"equalTo": 2}, ["mid"]),
    ],
)
def test_value_ordering_contract(client, query, expected_keys):
    assert client.put("/scores.json", json={"low": 1, "mid": 2, "high": 3}).status_code == 200
    assert client.put("/set-index", params={"path": "scores"}, json=".value").status_code == 200

    response = client.get("/scores.json", params={"orderBy": '"$value"', **query})

    assert response.status_code == 200
    assert list(response.json()) == expected_keys


def test_nested_dictionary_query_contract(client, ordered_records):
    response = client.get(
        "/records/a/tags.json",
        params={"orderBy": '"$key"', "startAt": '"b"', "endAt": '"c"'},
    )
    assert response.status_code == 200
    assert response.json() == {"b": "beta", "c": "gamma"}

    assert client.put("/set-index", params={"path": "records/a/tags"}, json=".value").status_code == 200
    response = client.get(
        "/records/a/tags.json",
        params={"orderBy": '"$value"', "startAt": '"b"', "endAt": '"gamma"'},
    )
    assert response.status_code == 200
    assert response.json() == {"b": "beta", "c": "gamma"}


def test_query_rejects_conflicting_limits(client, ordered_records):
    response = client.get(
        "/records.json",
        params={"orderBy": '"$key"', "limitToFirst": 1, "limitToLast": 1},
    )

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "limitToFirst and limitToLast cannot both be defined"


@pytest.mark.parametrize("query", [{"startAt": '"a"'}, {"endAt": '"c"'}])
def test_query_bounds_require_ordering(client, ordered_records, query):
    response = client.get("/records.json", params=query)

    assert response.status_code == 400
    assert response.json()["detail"]["error"] == "orderBy must be defined when other query parameters are defined"


def test_index_rules_are_upserted_and_root_is_normalized(client):
    assert client.put("/set-index", params={"path": "records"}, json="name").json() == {
        "path": "records",
        "indexOn": "name",
    }
    assert client.put("/set-index", params={"path": "records"}, json=["name", "score"]).json() == {
        "path": "records",
        "indexOn": ["name", "score"],
    }
    assert client.put("/set-index", json=".value").json() == {
        "path": "__root__",
        "indexOn": ".value",
    }

    assert client.get("/get-rules").json() == {
        "records": ["name", "score"],
        "indexOn": ".value",
    }


def test_deep_writes_target_the_existing_record(client):
    assert client.put("/records.json", json={"a": {"profile": {"name": "Ada"}}}).status_code == 200

    assert client.put("/records/a/profile/contact/email.json", json="ada@example.com").json() == "ada@example.com"
    response = client.post("/records/a/profile/messages.json", json={"text": "hello"})
    message_id = response.json()["name"]
    assert (
        client.patch(
            "/records/a/profile.json",
            json={"name": "Grace", "contact/phone": "1234"},
        ).status_code
        == 200
    )

    record = client.get("/records/a.json").json()
    assert record == {
        "profile": {
            "name": "Grace",
            "contact": {"email": "ada@example.com", "phone": "1234"},
            "messages": {message_id: {"text": "hello"}},
        }
    }


def test_patch_can_create_records_and_mix_direct_and_deep_paths(client):
    assert (
        client.patch(
            "/records.json",
            json={
                "a": {"name": "Ada"},
                "b/name": "Grace",
                "b/contact/email": "grace@example.com",
            },
        ).status_code
        == 200
    )

    assert client.get("/records.json").json() == {
        "a": {"name": "Ada"},
        "b": {"name": "Grace", "contact": {"email": "grace@example.com"}},
    }


def test_delete_is_idempotent_and_empty_collections_are_supported(client):
    assert client.delete("/missing/path.json").status_code == 200
    assert client.put("/empty.json", json={}).json() == {}
    assert client.get("/empty.json").json() == {}


@pytest.mark.parametrize("method", ["post", "put", "patch"])
def test_write_routes_reject_missing_bodies(client, method):
    response = getattr(client, method)("/records.json")

    assert response.status_code == 422
