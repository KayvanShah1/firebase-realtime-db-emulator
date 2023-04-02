from fastapi import HTTPException, status
from collections.abc import MutableMapping


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
