import json
import uuid
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from mongomock_motor import AsyncMongoMockClient
from pymongo import MongoClient

from app.core.settings import settings
from app.db.database import close_database, configure_database
from app.main import create_app

FIXTURES_DIR = Path(__file__).parent / "fixtures"
REAL_DATABASE_PREFIX = "firemongo_test_"


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--real-mongodb",
        action="store_true",
        default=False,
        help="Run opt-in tests against MONGODB_URI using an isolated temporary database",
    )


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
def real_db_client(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch):
    if not request.config.getoption("--real-mongodb"):
        pytest.skip("pass --real-mongodb to run tests against MONGODB_URI")
    if settings.mongodb_uri is None:
        pytest.fail("MONGODB_URI must be configured to run real MongoDB tests")

    database_name = f"{REAL_DATABASE_PREFIX}{uuid.uuid4().hex[:20]}"
    mongodb_uri = settings.mongodb_uri.get_secret_value()
    monkeypatch.setattr(settings, "database_name", database_name)

    try:
        with TestClient(create_app()) as test_client:
            yield test_client
    finally:
        close_database(force=True)
        cleanup_client = MongoClient(
            mongodb_uri,
            serverSelectionTimeoutMS=10_000,
            appname="firemongo-pytest-cleanup",
        )
        try:
            test_database = cleanup_client[database_name]
            for collection_name in test_database.list_collection_names():
                test_database[collection_name].drop()
        finally:
            cleanup_client.close()


@pytest.fixture
def nested_users_payload() -> dict[str, Any]:
    return load_json_fixture("users_nested.json")


@pytest.fixture
def sample_data_payload() -> dict[str, Any]:
    return load_json_fixture("sample_data.json")


@pytest.fixture
def sample_documents() -> list[dict[str, Any]]:
    return load_json_fixture("sample.json")
