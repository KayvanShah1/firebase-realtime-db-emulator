from fastapi import HTTPException, status
from app.core import settings


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
            status_code=status.HTTP_400_BAD_REQUEST, detail="Data cannot be None"
        )


def replace_prefix(path: str):
    return path.replace(settings.API_V1_PREFIX, "")
