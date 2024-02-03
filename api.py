from fastapi import Depends, APIRouter, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlmodel import select
from pydantic import BaseModel
from sessions import authorize, hash_password, verify_password, new_session
from view_levels import *
from db.models import *
from db.models import User as UserClass
from db import Database
import db
import io
import base64
import hashlib

router = APIRouter(
    prefix="/api",
    tags=["api"],
)


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
    nickname: Optional[str]
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

    async with db.begin_nested():
        user = User(**req.model_dump())
        db.add(user)

    await db.refresh(user)
    assert user.id is not None

    async with db.begin_nested():
        userpw = UserPassword(id=user.id, passhash=hash_password(req.password))
        db.add(userpw)

    return new_session(db, user.id)


@router.get("/users/me")
async def get_self(
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> UserView:
    """
    This function returns the currently authenticated user.
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@router.patch("/users/me")
async def update_user(
    req: RegisterRequest,
    me_id: int = Depends(authorize),
    db: Database = Depends(db.use),
) -> User:
    """
    Updates the specified authenticated user
    """
    user = User(id=me_id, **req.model_dump())
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


# @router.delete("/users/delete")
# async def delete_user()


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


class HouseRequest(BaseModel):
    lat: float
    lon: float


@router.get("/houses/{house_id}")
async def get_house(
    house_id: int,
    db: Database = Depends(db.use),
    # me: str = Depends(authorize),
) -> House:
    """
    This function returns a house by ID.
    """
    # TODO: implement permission checking
    query = select(House).where(House.id == house_id)
    house = (await db.exec(query)).one()
    return house

    # raise HTTPException(status_code=501, detail="Not implemented")


@router.post("/houses")
async def create_house(req: HouseRequest, db: Database = Depends(db.use)) -> House:
    """
    Creates a new house
    """
    # TODO: assert that you don't already have a house
    house = House(**req.model_dump())
    db.add(house)
    await db.commit()
    await db.refresh(house)
    return house


@router.patch("/houses/{house_id}")
async def update_house(
    house_id: int, req: HouseRequest, db: Database = Depends(db.use)
) -> House:
    """
    Updates the information of a current house
    """
    query = select(House).where(House.id == house_id)
    house = (await db.exec(query)).one()
    house.lat = req.lat
    house.lon = req.lon
    db.add(house)
    await db.commit()
    await db.refresh(house)
    return house


@router.delete("/houses/{house_id}")
async def delete_house(house_id: int, db: Database = Depends(db.use)) -> House:
    """
    Deletes a house from the database
    """
    query = select(House).where(House.id == house_id)
    house = (await db.exec(query)).one()
    await db.delete(house)
    await db.commit()
    return house


@router.get(
    "/assets/{asset_hash}",
    responses={
        200: {
            "content": {
                "application/octet-stream": {},
                "application/json": None,
            },
            "description": "Return the bytes of the asset in body",
        }
    },
)
async def get_asset(
    asset_hash: str,
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> StreamingResponse:
    """
    This function returns an asset by hash.
    """

    asset = (await db.exec(select(Asset).where(Asset.hash == asset_hash))).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Not found")

    stream = io.BytesIO(asset.data)
    return StreamingResponse(stream, media_type=asset.content_type)


class GetAssetMetadataResponse(BaseModel):
    content_type: str
    alt: str | None = None


@router.get("/assets/{asset_hash}/metadata")
async def get_asset_metadata(
    asset_hash: str,
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> GetAssetMetadataResponse:
    """
    This function returns metadata for an asset by hash.
    """

    asset = (await db.exec(select(Asset).where(Asset.hash == asset_hash))).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Not found")

    return GetAssetMetadataResponse(**asset.model_dump())


class UploadFileResponse(BaseModel):
    hash: str
    content_type: str
    alt: str | None = None


@router.post("/assets")
async def upload_asset(
    file: UploadFile,
    alt: Optional[str] = Form(),
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> UploadFileResponse:
    """
    Uploads an asset and returns its hash.
    """
    UPLOAD_LIMIT = 1024 * 1024 * 5  # 5 MB

    if file.content_type is None:
        raise HTTPException(status_code=400, detail="Content-Type header is required")

    if file.size is None or file.size > UPLOAD_LIMIT:
        raise HTTPException(status_code=400, detail="File is too large")

    data = await file.read()
    hash = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).decode("utf-8")
    content_type = file.content_type

    asset = Asset(
        hash=hash,
        data=data,
        content_type=content_type,
        alt=alt if alt else None,
    )
    db.add(asset)

    return UploadFileResponse(**asset.model_dump())


@router.get("/chat/groups")
async def get_chat_groups(
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> list[Group]:
    """
    This function returns chat groups that the current user currently has an
    open DM with.
    """
    raise HTTPException(status_code=501, detail="Not implemented")


@router.get("/chat/messages/{group_id}")
async def get_chat_messages(
    group_id: int,
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> list[ChatMessage]:
    """
    This function returns chat messages for a group that the current user is in.
    """
    # TODO: assert that the user is either in a GroupRelationship with open_dms
    # true or they belong in their group.
    raise HTTPException(status_code=501, detail="Not implemented")


class SendChatMessageRequest(BaseModel):
    content: Union[ChatContentText, ChatContentSticker, ChatContentImage] = Field(
        discriminator="type"
    )


@router.post("/chat/messages/{group_id}")
async def send_chat_message(
    group_id: int,
    req: SendChatMessageRequest,
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> ChatMessage:
    """
    This function sends a chat message to a group.
    """
    if isinstance(req.content, ChatContentSticker):
        await assert_asset_hash(db, req.content.asset_hash)
    if isinstance(req.content, ChatContentImage):
        await assert_asset_hash(db, req.content.asset_hash)

    raise HTTPException(status_code=501, detail="Not implemented")


async def assert_asset_hash(db: Database, hash: str):
    asset = (await db.exec(select(Asset.hash).where(Asset.hash == hash))).first()
    if asset is None:
        raise HTTPException(status_code=400, detail="Asset hash does not exist")
