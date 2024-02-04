from fastapi import HTTPException
from db import Database
from db.models import *
from sqlmodel import select


async def owns_house(db: Database, me_id: int, house_id: int) -> bool:
    """
    Returns whether the user with the given `me_id` owns the house with the given
    `house_id`.
    """
    group_house_id = (
        await db.exec(
            select(Group.house_id)
            .join(User)
            .where(User.id == me_id and User.group_id == Group.id)
        )
    ).first()
    if group_house_id is None:
        print("group_house_id is None")
        return False

    print(f"group_house_id: {group_house_id}")
    return group_house_id == house_id


async def assert_owns_house(db: Database, me_id: int, house_id: int) -> None:
    """
    Asserts that the user with the given `me_id` owns the house with the given
    `house_id`.
    """
    if not await owns_house(db, me_id, house_id):
        raise HTTPException(status_code=403, detail="You do not own this house")
