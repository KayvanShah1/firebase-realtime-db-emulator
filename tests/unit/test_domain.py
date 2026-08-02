import pytest
from pydantic import ValidationError

from app.domain.firebase_path import FirebasePath
from app.domain.query import QuerySpec

pytestmark = pytest.mark.unit


def test_firebase_path_exposes_storage_coordinates():
    path = FirebasePath.parse("/users/42/profile/name/")

    assert path.raw == "users/42/profile/name"
    assert path.collection == "users"
    assert path.record_id == "42"
    assert path.child_segments == ("profile", "name")
    assert path.mongo_value_path == "_fm_val.profile.name"
    assert path.mongo_parent_path == "_fm_val.profile"
    assert not path.is_collection
    assert path.append("first").raw == "users/42/profile/name/first"


def test_firebase_collection_path_has_no_record():
    path = FirebasePath.parse("users")

    assert path.is_collection
    assert path.record_id is None
    assert path.mongo_value_path == "_fm_val"
    assert path.mongo_parent_path == "_fm_val"


@pytest.mark.parametrize("path", ["", "/", "users//name"])
def test_firebase_path_rejects_empty_segments(path):
    with pytest.raises(ValueError, match="empty"):
        FirebasePath.parse(path)


def test_query_spec_accepts_api_aliases_and_decodes_values():
    query = QuerySpec.model_validate(
        {
            "orderBy": '"score"',
            "limitToFirst": 2,
            "equalTo": "42",
            "startAt": '"Ada"',
        }
    )

    assert query.order_by == '"score"'
    assert query.normalized_order_by == "score"
    assert query.limit_to_first == 2
    assert query.equal_to == 42
    assert query.start_at == "Ada"
    assert query.validation_error() is None


def test_query_spec_reports_dependent_options_without_ordering():
    query = QuerySpec(limit_to_first=1)

    assert query.validation_error() == "orderBy must be defined when other query parameters are defined"


def test_query_spec_rejects_negative_limits():
    with pytest.raises(ValidationError):
        QuerySpec(limit_to_first=-1)
