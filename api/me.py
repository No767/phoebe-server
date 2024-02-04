from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlmodel import select
from utils.sessions import authorize, hash_password, verify_password, new_session
from api.assets import assert_asset_hash
from db import Database
from db.models import *
import db

router = APIRouter(tags=["me"])


class LoginRequest(BaseModel):
    email: str
    password: str


@router.post("/login")
async def login(
    req: LoginRequest,
    db: Database = Depends(db.use),
) -> Session:
    """
    This function logs in a user and returns a session token.
    """
    user = (await db.exec(select(User).where(User.email == req.email))).first()
    if user is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    passhash = (
        await db.exec(select(UserPassword.passhash).where(UserPassword.id == user.id))
    ).one()
    if not verify_password(req.password, passhash):
        raise HTTPException(status_code=401, detail="Unauthorized")

    assert user.id is not None
    return new_session(db, user.id)


class RegisterRequest(BaseModel):
    """
    This class is used to register a new user.
    """

    email: str
    password: str

    bio: str
    color: str
    avatar_hash: Optional[str] = None
    nickname: Optional[str] = None
    preferred_name: str
    genders: list[str]
    pronouns: list[str]
    sexual_orientations: list[str]


@router.post("/register")
async def register(
    req: RegisterRequest,
    db: Database = Depends(db.use),
) -> Session:
    """
    This function registers a new user and returns a session token.
    """

    if req.avatar_hash is not None:
        await assert_asset_hash(db, req.avatar_hash)

    if req.nickname is None:
        req.nickname = req.preferred_name

    async with db.begin_nested():
        user = User(**req.model_dump())
        db.add(user)

    await db.refresh(user)
    assert user.id is not None

    async with db.begin_nested():
        userpw = UserPassword(id=user.id, passhash=hash_password(req.password))
        db.add(userpw)

    return new_session(db, user.id)


class UserResponse(BaseModel):
    id: int = Field(default_factory=generate_id, primary_key=True)
    email: str
    bio: str
    color: str
    avatar_hash: Optional[str]
    preferred_name: str
    nickname: str
    genders: list[str]
    pronouns: list[str]
    sexual_orientations: list[str]
    group: Optional[Group]


@router.get("/users/me")
async def get_self(
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> UserResponse:
    """
    This function returns the currently authenticated user.
    """
    user = (await db.exec(select(User).where(User.id == me_id))).one()
    group = None

    if user.group_id is not None:
        group = (await db.exec(select(Group).where(Group.id == user.group_id))).one()

    return UserResponse(**user.model_dump(), group=group)


@router.patch("/users/me")
async def update_user(
    req: RegisterRequest,
    me_id: int = Depends(authorize),
    db: Database = Depends(db.use),
) -> User:
    """
    Updates the specified authenticated user
    """
    user = (await db.exec(select(User).where(User.id == me_id))).one()
    password = (
        await db.exec(select(UserPassword).where(UserPassword.id == me_id))
    ).one()

    if req.nickname is None:
        req.nickname = req.preferred_name

    for key, value in req.model_dump().items():
        match key:
            case "password":
                password.passhash = hash_password(value)
            case "avatar_hash":
                if value is not None:
                    await assert_asset_hash(db, value)
                setattr(user, key, value)
            case _:
                setattr(user, key, value)

    db.add(user)
    db.add(password)

    await db.commit()
    await db.refresh(user)

    return user


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
