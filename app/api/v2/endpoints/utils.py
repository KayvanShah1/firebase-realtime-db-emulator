from fastapi import HTTPException, status


async def _if_structure_exists(collection, key: str) -> bool:
    """_summary_

    Args:
        collection (_type_): _description_
        key (str): _description_

    Returns:
        _type_: _description_
    """
    resp = await collection.find_one({key: {"$exists": True}})
    if resp is not None:
        return True
    return False


def _check_empty_payload(payload) -> Exception:
    """_summary_

    Args:
        payload (_type_): _description_

    Raises:
        HTTPException: _description_
    """
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data cannot be None",
        )


def _check_data_type_for_root(data) -> Exception:
    if type(data) is not dict:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Data type other than dict is not supported in MongoDB",
        )
