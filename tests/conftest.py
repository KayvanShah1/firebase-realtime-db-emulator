import json
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient

from app.db.database import close_database, configure_database
from app.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"


def load_json_fixture(filename: str) -> Any:
    with (FIXTURES_DIR / filename).open(encoding="utf-8") as fixture_file:
        return json.load(fixture_file)


@pytest.fixture
def mongo_client():
    client = AsyncMongoMockClient()
    configure_database(client, f"test_{uuid.uuid4().hex}")
    try:
        yield client
    finally:
        close_database(force=True)


@pytest.fixture
def client(mongo_client):
    with TestClient(create_app()) as test_client:
        yield test_client


@pytest.fixture
def nested_users_payload() -> dict[str, Any]:
    return load_json_fixture("users_nested.json")


@pytest.fixture
def sample_data_payload() -> dict[str, Any]:
    return load_json_fixture("sample_data.json")


@pytest.fixture
def sample_documents() -> list[dict[str, Any]]:
    return load_json_fixture("sample.json")
