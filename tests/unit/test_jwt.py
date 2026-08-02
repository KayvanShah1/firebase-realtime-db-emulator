import pytest

from app.core.jwt import create_access_token, verify_access_token

pytestmark = pytest.mark.unit


def test_access_token_round_trip():
    token = create_access_token({"id": "user-123"})

    assert verify_access_token(token).id == "user-123"
