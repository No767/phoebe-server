from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from sessions import authorize
from db import Database, geospatial
from db.models import *
from db.geospatial import search_nearest_houses
import db
from viewlevels.house import assert_owns_house

router = APIRouter(tags=["houses"])


# @router.get("/houses/{house_id}")
# async def get_house(
#     house_id: int,
#     db: Database = Depends(db.use),
#     # me: str = Depends(authorize),
# ) -> House:
#     """
#     This function returns a house by ID.
#     """
#     # TODO: implement permission checking
#     query = select(House).where(House.id == house_id)
#     house = (await db.exec(query)).one()
#     return house


class CreateHouseRequest(BaseModel):
    lat: float
    lon: float
    description: str


@router.post("/houses")
async def create_house(
    req: CreateHouseRequest,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> House:
    """
    Creates a new house
    """
    user = (await db.exec(select(User).where(User.id == me_id))).one()
    if user.group_id is None:
        raise HTTPException(
            status_code=400,
            detail="You must be in a group to create a house for that group.",
        )

    group = (await db.exec(select(Group).where(Group.id == user.group_id))).one()
    if group.house_id is not None:
        raise HTTPException(
            status_code=400,
            detail="The group you are in already has a house.",
        )

    async with db.begin_nested():
        house = House(**req.model_dump())
        db.add(house)

    async with db.begin_nested():
        group.house_id = house.id
        db.add(group)

    await db.refresh(house)
    return house


@router.patch("/houses/{house_id}")
async def update_house(
    house_id: int,
    req: CreateHouseRequest,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> House:
    """
    Updates the information of a current house
    """
    await assert_owns_house(db, me_id, house_id)

    query = select(House).where(House.id == house_id)
    house = (await db.exec(query)).one()
    for k, v in req.model_dump().items():
        setattr(house, k, v)

    db.add(house)
    await db.commit()
    await db.refresh(house)

    return house


@router.delete("/houses/{house_id}")
async def delete_house(
    house_id: int,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> None:
    """
    Delete the house from your group.
    """
    await assert_owns_house(db, me_id, house_id)

    group = (await db.exec(select(Group).where(Group.house_id == house_id))).one()
    group.house_id = None
    db.add(group)

    query = select(House).where(House.id == house_id)
    house = (await db.exec(query)).one()
    await db.delete(house)
