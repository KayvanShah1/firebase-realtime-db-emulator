import pytest
from fastapi import HTTPException

from app.api.v1.endpoints.utils import _check_empty_payload as check_v1_payload
from app.api.v2.endpoints.utils import (
    _check_empty_payload as check_v2_payload,
)
from app.api.v2.endpoints.utils import (
    flatten_dict,
    get_items_between_range,
    order_by_key,
    order_by_value,
    unwrap_path_to_dict,
)

pytestmark = pytest.mark.unit


def test_flatten_and_unwrap_nested_paths():
    nested = {"user": {"name": {"first": "Ada"}, "age": 36}}

    assert flatten_dict(nested) == {"user.name.first": "Ada", "user.age": 36}
    assert unwrap_path_to_dict({"user/name/first": "Ada", "user/age": 36}) == nested


@pytest.mark.parametrize(
    ("items", "start", "end", "expected"),
    [
        ([1, 3, 5, 8], 3, 5, [3, 5]),
        (["Ada", "Grace", "Linus"], "G", "L", ["Grace", "Linus"]),
    ],
)
def test_get_items_between_range(items, start, end, expected):
    assert get_items_between_range(items, start, end) == expected


def test_get_items_between_range_rejects_mixed_bounds():
    with pytest.raises(ValueError, match="same type"):
        get_items_between_range([1, 2, 3], 1, "3")


def test_ordering_helpers():
    assert order_by_key(["c", "a", "b"], startAt="b") == ["c", "b"]
    assert order_by_value({"none": None, "two": 2, "one": 1}) == {
        "none": None,
        "one": 1,
        "two": 2,
    }


@pytest.mark.parametrize(
    ("checker", "status_code"),
    [(check_v1_payload, 400), (check_v2_payload, 422)],
)
def test_empty_payload_validation(checker, status_code):
    with pytest.raises(HTTPException) as error:
        checker(None)

    assert error.value.status_code == status_code
