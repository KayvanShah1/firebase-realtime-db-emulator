import pytest

from app.domain.query import QuerySpec
from app.domain.query_engine import FirebaseQueryEngine

pytestmark = pytest.mark.unit


def test_value_ordering_follows_json_type_order():
    values = {
        "string": "value",
        "number": 1,
        "true": True,
        "false": False,
        "null": None,
    }

    result = FirebaseQueryEngine().apply(values, QuerySpec(order_by='"$value"'))

    assert list(result) == ["null", "false", "true", "number", "string"]


def test_child_ordering_filters_missing_children_before_limiting():
    values = {
        "missing": {"other": 0},
        "third": {"score": 3},
        "first": {"score": 1},
        "second": {"score": 2},
    }
    query = QuerySpec(order_by='"score"', start_at="2", limit_to_first=1)

    result = FirebaseQueryEngine().apply(values, query)

    assert result == {"second": {"score": 2}}
