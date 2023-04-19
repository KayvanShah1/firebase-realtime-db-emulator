import re

from typing import Dict, List, Union, Any
from fastapi import HTTPException, status
from collections.abc import MutableMapping

from app.db.database import get_collection


async def _if_structure_exists(collection, key: str) -> bool:
    """
    Checks if a given key exists in a collection.

    Args:
        collection: A MongoDB collection to search
        key: The key to search for in the collection

    Returns:
        bool: True if the key exists in the collection, False otherwise
    """
    resp = await collection.find_one({key: {"$exists": True}})
    if resp is not None:
        return True
    return False


def _check_empty_payload(payload) -> Exception:
    """Checks whether the payload is empty or not.

    Args:
        payload: A payload to be checked.

    Raises:
        HTTPException: If the payload is None, raises an HTTPException with a status code of
            HTTP 422 Unprocessable Entity and a message "Data cannot be None".
    """
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data cannot be None",
        )


def _check_data_type_for_root(data) -> Exception:
    """Checks whether the data type is a dictionary or not.

    Args:
        data: A data to be checked.

    Raises:
        HTTPException: If the data type is not a dictionary, raises an HTTPException with a status code of
            HTTP 422 Unprocessable Entity and a message "Invalid data; couldn't parse JSON object.
            Are you sending a JSON object with valid key names?".
    """
    if type(data) is not dict:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={
                "error": "Invalid data; couldn't parse JSON object. Are you sending a JSON object with valid key names?"
            },
        )


def _flatten_dict_gen(d, parent_key, sep):
    """
    A generator function that recursively flattens a nested dictionary into a dictionary with no nested keys.

    Args:
        d (dict): The dictionary to flatten.
        parent_key (str): The parent key to use for flattening.
        sep (str): The separator to use between parent and child keys.

    Yields:
        tuple: A tuple of key-value pairs in the flattened dictionary.

    Returns:
        None
    """
    for k, v in d.items():
        new_key = parent_key + sep + k if parent_key else k
        if isinstance(v, MutableMapping):
            yield from flatten_dict(v, new_key, sep=sep).items()
        else:
            yield new_key, v


def flatten_dict(d: MutableMapping, parent_key: str = "", sep: str = "."):
    """
    Flattens a nested dictionary into a dictionary with no nested keys by calling the _flatten_dict_gen function.

    Args:
        d (MutableMapping): The dictionary to flatten.
        parent_key (str, optional): The current parent key to be used for flattening. Defaults to "".
        sep (str, optional): The separator to be used between parent and child keys in the flattened dictionary.
            Defaults to ".".

    Returns:
        dict: A flattened dictionary.

    """
    return dict(_flatten_dict_gen(d, parent_key, sep))


def unwrap_path_to_dict(data: dict) -> dict:
    """
    Convert a flat dictionary with slash-separated keys into a nested dictionary.

    Args:
        data (dict): The dictionary to convert. It should have string keys with one
            or more slash characters (/) separating the levels of the nested structure.
            The values can be of any type.

    Returns:
        dict: A new dictionary with the same values as the input dictionary, but with
            nested dictionaries created based on the slash-separated keys.

    Example:
        >>> data = {"8/lastName": "Gopalnath", "5/phoneNumber": "5555555555"}
        >>> convert_to_nested_dict(data)
        {
            "8": {"lastName": "Gopalnath"},
            "5": {"phoneNumber": "5555555555"}
        }
    """
    nested_dict = {}
    for key, value in data.items():
        keys = key.split("/")
        current_dict = nested_dict
        for k in keys[:-1]:
            current_dict = current_dict.setdefault(k, {})
        current_dict[keys[-1]] = value
    return nested_dict


async def check_index(path: str = None):
    """Retrieves the index expression for an existing index document for a given path in the __fm_rules__ collection.

    Args:
        path (str, optional): The path to retrieve the index for. Defaults to None.

    Returns:
        str | dict | list | None: The index expression if the index document exists for the given path, otherwise None.
    """
    index_collection = get_collection("__fm_rules__")

    if path is None:
        path = "__root__"

    index_doc = await index_collection.find_one({"path": path})
    if index_doc is not None:
        return index_doc["indexOn"]
    return None


def get_items_between_indexes(
    items: List[str], startAt: Union[str, int], endAt: Union[str, int]
) -> List[str]:
    """
    Get items between two indexes (inclusive).

    Args:
        items (List[Union[str, int]]): The list of items to search.
        startAt (Union[str, int]): The item to start searching from.
        endAt (Union[str, int]): The item to end searching at.

    Returns:
        List[Union[str, int]]: The list of items between the two indexes (inclusive).

    Example:
        >>> items = ["1", "2", "798", "yuyuy", 98, 0, 46, "nm"]
        >>> get_items_between_indexes(items, "2", 98)
        ['2', '798', 'yuyuy', 98]
    """
    start_index = next(
        (i for i, item in enumerate(items) if str(item).startswith(startAt)), None
    )
    end_index = next(
        (i for i, item in enumerate(items) if str(item).startswith(endAt)), None
    )

    if start_index is None or end_index is None:
        return []

    if start_index > end_index:
        start_index, end_index = end_index, start_index

    return items[start_index : end_index + 1]


def get_items_between_range(
    items: List[str], startAt: Union[str, int, None], endAt: Union[str, int, None]
) -> List:
    """Get items between two indexes (inclusive).

    Args:
        items (List[Union[str, int]]): The list of items to search.
        startAt (Union[str, int]): The item to start searching from.
        endAt (Union[str, int]): The item to end searching at.

    Raises:
        ValueError: Both range should be of same data type

    Returns:
        List[Union[str, int]]: The list of items between the two indexes (inclusive).
    """
    if isinstance(startAt, (str, type(None))) and isinstance(endAt, (str, type(None))):
        startAt = startAt if startAt is not None else "a"
        endAt = endAt if endAt is not None else "z"

        startAt = startAt.lower()[0] if len(startAt) > 1 else startAt.lower()
        endAt = endAt.lower()[0] if len(endAt) > 1 else endAt.lower()

        pattern = re.compile(f"^[{startAt}-{endAt}]" + "{1}", re.IGNORECASE)
        items = (item for i, item in enumerate(items) if pattern.search(item))

    elif isinstance(startAt, (int, type(None))) and isinstance(
        endAt, (int, type(None))
    ):
        items = (
            item
            for i, item in enumerate(items)
            if isinstance(item, int)
            and (startAt is None or item >= startAt)
            and (endAt is None or item <= endAt)
        )

    else:
        raise ValueError("startAt and endAt should have the same type")

    return list(items)


def order_by_key(items: List[str], startAt: Any = None, endAt: Any = None) -> List:
    """
    Sorts a list of strings lexicographically based on their keys.

    Args:
        items: A list of strings to be sorted.
        startAt: Optional. A string specifying the lower bound for the sorted items. Only items with keys greater than
            or equal to startAt are included in the result. Defaults to None.
        endAt: Optional. A string specifying the upper bound for the sorted items. Only items with keys less than or
            equal to endAt are included in the result. Defaults to None.

    Returns:
        A list of strings sorted lexicographically based on their keys and filtered based on startAt and endAt.
    Raises:
        ValueError: If startAt and endAt have different types.

    The function sorts the list of strings based on their keys in lexicographically ascending order. If startAt is
    specified, only items with keys greater than or equal to startAt are included in the result. If endAt is specified,
    only items with keys less than or equal to endAt are included in the result. If startAt and endAt are both
    specified, only items with keys between startAt and endAt are included. If startAt or endAt is not specified,
    all items with keys greater than or equal to startAt and/or less than or equal to endAt are included.

    """
    if startAt is not None:
        items = (item for item in items if item >= startAt)
    if endAt is not None:
        items = (item for item in items if item <= endAt)

    return list(items)


def order_by_value(
    dictionary: Dict[Any, Any], startAt: Any = None, endAt: Any = None
) -> Dict[Any, Any]:
    """Sorts a dictionary by the values, and returns a new dictionary with the same keys, but sorted by the values.

    Args:
        dictionary (Dict): A dictionary to be sorted.
        startAt (Any): Optional. A string specifying the lower bound for the sorted items. Only items with keys greater
            than or equal to startAt are included in the result. Defaults to None.
        endAt (Any:): Optional. A string specifying the upper bound for the sorted items. Only items with keys less
            than or equal to endAt are included in the result. Defaults to None.

    Returns:
        Dict: A new dictionary with the same keys as the input dictionary, but sorted by the values in ascending order.
    """

    def sort_key(item: Any) -> Any:
        """Returns a tuple that can be used as the key for sorting items.

        Args:
            item (Any): A tuple containing a key-value pair from the input dictionary.

        Returns:
            Tuple: A tuple that can be used as the key for sorting items.
        """
        if item[1] is None:
            return (0, None)
        if isinstance(item[1], bool):
            return (1, not item[1], item[0])
        elif isinstance(item[1], (int, float)):
            return (2, item[1], item[0])
        elif isinstance(item[1], str):
            return (3, item[1], item[0])
        elif isinstance(item[1], list):
            return (4, [sort_key((i, x)) for i, x in enumerate(item[1])], item[0])
        elif isinstance(item[1], dict):
            return (5, [sort_key((k, v)) for k, v in item[1].items()], item[0])
        else:
            return (6, item[0])

    sorted_items = sorted(dictionary.items(), key=sort_key)
    # Filter out items
    if startAt is not None:
        sorted_items = [(k, v) for k, v in sorted_items if str(v) >= str(startAt)]
    if endAt is not None:
        sorted_items = [(k, v) for k, v in sorted_items if str(v) <= str(endAt)]

    sorted_items = {k: v for k, v in sorted_items}
    return sorted_items
