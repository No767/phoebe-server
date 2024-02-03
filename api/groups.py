from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from db import Database
from db.models import *
from sessions import authorize
from viewlevels.user import UserView, user_view_from_db
import db

router = APIRouter(tags=["groups"])


class GroupResponse(Group):
    people: list[UserView] = Field(sa_column=Column(JSON))


async def group_response(db: Database, me_id: int, group: Group) -> GroupResponse:
    people = (await db.exec(select(User).where(User.group_id == group.id))).all()
    people = [await user_view_from_db(db, me_id, person) for person in people]
    return GroupResponse(people=people, **group.model_dump())


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

    return await group_response(db, me_id, group)


class CreateGroupRequest(BaseModel):
    name: str
    bio: str
    color: str
    icon_hash: Optional[str] = None


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
async def delete_group(group_id: int, db: Database = Depends(db.use)) -> Group:
    """
    Deletes a group from the database using the specified ID
    """
    # TODO: Make sure that the user has proper permissions to delete stuff
    query = select(Group).where(Group.id == group_id)
    group = (await db.exec(query)).one()
    await db.delete(group)
    await db.commit()
    return group


@router.patch("/groups/{group_id}")
async def update_group(
    group_id: int,
    req: CreateGroupRequest,
    db: Database = Depends(db.use),
    # me: str = Depends(authorize),
) -> Group:
    """
    Updates a group using the specified ID
    """
    query = select(Group).where(Group.id == group_id)
    res = (await db.exec(query)).one()
    for k, v in req.model_dump().items():
        setattr(res, k, v)
    db.add(res)
    await db.commit()
    await db.refresh(res)
    return res
