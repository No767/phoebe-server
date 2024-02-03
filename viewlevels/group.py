from fastapi import HTTPException
from sqlmodel import select
from db import Database
from db.models import *
import db


async def owns_group(
    db: Database,
    me_id: int,
    group_id: int,
) -> bool:
    """
    This function returns True if the current user owns the specified group.
    """
    return (
        await db.exec(
            select(User.group_id).where(User.id == me_id and User.group_id == group_id)
        )
    ).first() is not None


async def assert_owns_group(
    db: Database,
    me_id: int,
    group_id: int,
) -> None:
    """
    This function raises an HTTPException if the current user does not own the
    specified group.
    """
    if not await owns_group(db, me_id, group_id):
        raise HTTPException(
            status_code=403,
            detail="You do not own this group",
        )


async def group_level(
    db: Database,
    me_id: int,
    group_id: int,
    default=AccessLevel.PUBLIC,
) -> AccessLevel:
    """
    This function returns the access level of the current user in the specified
    group.

    If the user is part of this group, then the highest access level is implied.
    """
    if await owns_group(db, me_id, group_id):
        return AccessLevel.HIGHEST

    relationship = (
        await db.exec(
            select(GroupRelationship).where(
                GroupRelationship.user_id == me_id
                and GroupRelationship.group_id == group_id
            )
        )
    ).first()
    if relationship is None:
        return default

    return relationship.level


async def assert_group_level(
    db: Database,
    me_id: int,
    group_id: int,
    level: AccessLevel,
) -> None:
    """
    This function raises an HTTPException if the current user does not have the
    minimum specified access level in the specified group.

    If the user is part of this group, then the highest access level is implied.
    """
    actual_level = await group_level(db, me_id, group_id)
    if actual_level < level:
        raise HTTPException(
            status_code=403,
            detail="You do not have the required access level for this group",
        )
