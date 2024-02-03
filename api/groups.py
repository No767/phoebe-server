from fastapi import APIRouter, Depends
from sqlmodel import select
from db import Database
from db.models import *
import db

router = APIRouter(tags=["groups"])


@router.get("/groups/{group_id}")
async def get_group(
    group_id: int,
    db: Database = Depends(db.use),
    # me: str = Depends(authorize),
) -> Group:
    """
    This function returns a group by ID.
    """

    # TODO: implement permission checking
    query = select(Group).where(Group.id == group_id)
    group = (await db.exec(query)).one()
    return group


class GroupRequest(BaseModel):
    name: str
    bio: str


@router.post("/groups")
async def create_group(req: GroupRequest, db: Database = Depends(db.use)) -> Group:
    """
    Creates a group, which represents a group of users
    """
    # TODO: implement permissions checking
    group = Group(name=req.name, bio=req.bio)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


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
    req: GroupRequest,
    db: Database = Depends(db.use),
    # me: str = Depends(authorize),
) -> Group:
    """
    Updates a group using the specified ID
    """
    query = select(Group).where(Group.id == group_id)
    res = (await db.exec(query)).one()
    res.name = req.name
    res.bio = req.bio
    db.add(res)
    await db.commit()
    await db.refresh(res)
    return res
