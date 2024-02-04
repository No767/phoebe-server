from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from viewlevels.group import assert_group_level, assert_owns_group, group_level
from db import Database
from db.models import *
from sessions import authorize
from viewlevels.user import UserView, user_view_from_db
import db

router = APIRouter(tags=["groups"])


class GroupResponse(Group):
    people: list[UserView] = Field(sa_column=Column(JSON))
    interested: bool
    access_level: AccessLevel


async def group_response(db: Database, me_id: int, group: Group) -> GroupResponse:
    people = (await db.exec(select(User).where(User.group_id == group.id))).all()
    people = [await user_view_from_db(db, me_id, person) for person in people]
    level = await group_level(db, me_id, group.id)
    return GroupResponse(
        **group.model_dump(),
        people=people,
        interested=level >= AccessLevel.LEVEL1,
        access_level=level,
    )


@router.get("/groups/{group_id}")
async def get_group(
    group_id: int,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> GroupResponse:
    """
    This function returns a group by ID.
    """

    # TODO: implement permission checking
    query = select(Group).where(Group.id == group_id)
    group = (await db.exec(query)).first()
    if group is None:
        raise HTTPException(status_code=404, detail="Group not found")

    await assert_group_level(db, me_id, group.id, AccessLevel.LEVEL1)
    return await group_response(db, me_id, group)


@router.get("/groups/{group_id}/people")
async def get_group_people(
    group_id: int,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> list[UserView]:
    """
    This function returns a list of people in a group by ID.
    """
    await assert_group_level(db, me_id, group_id, AccessLevel.LEVEL1)
    people = (await db.exec(select(User).where(User.group_id == group_id))).all()
    return [await user_view_from_db(db, me_id, person) for person in people]


class CreateGroupRequest(BaseModel):
    name: str
    bio: str
    color: str
    icon_hash: Optional[str] = None
    lat: float
    lon: float
    has_house: bool = False


@router.post("/groups")
async def create_group(
    req: CreateGroupRequest,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> GroupResponse:
    """
    Creates a group, which represents a group of users
    """
    # TODO: implement permissions checking

    user = (await db.exec(select(User).where(User.id == me_id))).one()
    if user.group_id is not None:
        raise HTTPException(
            status_code=400,
            detail="You already have a group. You can only have one group at a time.",
        )

    async with db.begin_nested():
        # Create the actual group.
        group = Group(**req.model_dump())
        # Update the user's group_id
        user.group_id = group.id

        db.add(group)
        db.add(user)

    return await group_response(db, me_id, group)


@router.delete("/groups/{group_id}")
async def delete_group(
    group_id: int,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> Group:
    """
    Deletes a group from the database using the specified ID
    """
    # TODO: Make sure that the user has proper permissions to delete stuff
    query = select(Group).where(Group.id == group_id)
    group = (await db.exec(query)).one()
    await assert_owns_group(db, me_id, group.id)
    await db.delete(group)
    await db.commit()
    return group


@router.patch("/groups/{group_id}")
async def update_group(
    group_id: int,
    req: CreateGroupRequest,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> Group:
    """
    Updates a group using the specified ID
    """
    query = select(Group).where(Group.id == group_id)
    group = (await db.exec(query)).one()
    await assert_owns_group(db, me_id, group.id)

    for k, v in req.model_dump().items():
        setattr(group, k, v)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.post("/groups/{group_id}/interested")
async def group_interested(
    group_id: int,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> None:
    query = select(GroupRelationship).where(GroupRelationship.group_id == group_id)
    group = (await db.exec(query)).first()
    if group is not None and group.level >= AccessLevel.LEVEL1:
        raise HTTPException(
            status_code=400, detail="The interested group already is interested"
        )

    group_relationship = GroupRelationship(
        user_id=me_id,
        group_id=group_id,
        level=AccessLevel.LEVEL1,
    )
    db.add(group_relationship)
    await db.commit()
    await db.refresh(group_relationship)
        
    
    
