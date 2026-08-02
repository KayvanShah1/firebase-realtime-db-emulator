import pytest

pytestmark = pytest.mark.integration


def test_car_import_example_uses_local_deterministic_data(client):
    cars = {
        "car-1": {"name": "Roadster", "year": 2008},
        "car-2": {"name": "Model S", "year": 2012},
    }

    response = client.put("/cars.json", json=cars)

    assert response.status_code == 200
    assert client.get("/cars.json").json() == cars


def test_sample_documents_can_be_loaded_and_ordered_by_key(client, sample_documents):
    sample_payload = {document["_fm_id"]: document["_fm_val"] for document in sample_documents}
    assert client.put("/sample-dummy.json", json=sample_payload).status_code == 200

    response = client.get(
        "/sample-dummy.json",
        params={"orderBy": '"$key"', "limitToFirst": 2},
    )

    assert response.status_code == 200
    assert list(response.json()) == ["0605e7bc80884477b71a3675c77e5a80", "1"]


def test_sample_values_can_be_filtered_like_the_demo(client):
    values = {"first": "alpha", "second": "sigma", "third": "zeta"}
    assert client.put("/sample-dummy.json", json=values).status_code == 200
    assert (
        client.put(
            "/set-index",
            params={"path": "sample-dummy"},
            json=".value",
        ).status_code
        == 200
    )

    response = client.get(
        "/sample-dummy.json",
        params={"orderBy": '"$value"', "limitToLast": 2, "startAt": '"s"'},
    )

    assert response.status_code == 200
    assert response.json() == {"third": "zeta", "second": "sigma"}
