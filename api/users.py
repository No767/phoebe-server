from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from db import Database
from db.models import User, GroupRelationship, AccessLevel
from utils.sessions import authorize
from viewlevels.group import assert_group_level
from viewlevels.user import UserView, user_view_from_db
import db

router = APIRouter(tags=["users"])


@router.get("/users/{user_id}")
async def get_user(
    user_id: int,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> UserView:
    """
    This function returns the user with the specified id.
    It only allows access if the user has expressed interest in your group via
    `/groups/:id/interested`.
    """
    me = (await db.exec(select(User).where(User.id == me_id))).one()
    if me.group_id is None:
        raise HTTPException(status_code=403, detail="You do not have a group")

    # Ensure that the user has expressed interest in your group.
    await assert_group_level(db, user_id, me.group_id, AccessLevel.LEVEL1)

    user = (await db.exec(select(User).where(User.id == user_id))).one()
    return await user_view_from_db(db, me_id, user)


# The user id is the other person'd id
@router.post("/users/{user_id}/accept")
async def accept_group(
    user_id: int,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> None:
    # Need to update the group id on the user object
    # First check for the author's group
    relationship_query = (
        select(GroupRelationship)
        .join(User)
        .where(
            GroupRelationship.user_id == user_id
            and User.id == me_id
            and User.group_id == GroupRelationship.group_id
        )
    )
    relationship = (await db.exec(relationship_query)).first()
    # Don't look at this code.........
    if relationship is None:
        raise HTTPException(status_code=404, detail="Cannot find group to accept")

    if relationship.level < AccessLevel.LEVEL1:
        raise HTTPException(status_code=403, detail="Forbidden to access DMs")

    if relationship.open_dms:
        raise HTTPException(status_code=400, detail="Already accepted this group!")

    relationship.user_id = user_id
    relationship.open_dms = True
    db.add(relationship)
