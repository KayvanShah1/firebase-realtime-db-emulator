from typing import Any

from motor.motor_asyncio import AsyncIOMotorClient

_client: Any | None = None
_database: Any | None = None
_owns_client = False


def configure_database(
    client: Any,
    database_name: str = "firebase_db",
    *,
    owns_client: bool = False,
) -> None:
    """Configure the database used by the application.

    Tests can inject a compatible client without importing or contacting the
    development database.
    """
    global _client, _database, _owns_client
    _client = client
    _database = client[database_name]
    _owns_client = owns_client


def connect_database(mongodb_uri: str | None, database_name: str = "firebase_db") -> None:
    configure_database(
        AsyncIOMotorClient(mongodb_uri),
        database_name,
        owns_client=True,
    )


def is_database_configured() -> bool:
    return _database is not None


def get_database() -> Any:
    if _database is None:
        raise RuntimeError("Database has not been configured")
    return _database


def get_collection(collection_name: str) -> Any:
    return get_database()[collection_name]


def get_base_collection() -> Any:
    return get_collection("firebase_collection")


def close_database(*, force: bool = False) -> None:
    global _client, _database, _owns_client
    if _client is not None and (_owns_client or force):
        _client.close()
    _client = None
    _database = None
    _owns_client = False
