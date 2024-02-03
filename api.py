from fastapi import Depends, APIRouter, HTTPException, UploadFile
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


@router.get("/users/me")
async def get_self(
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> UserView:
    """
    This function returns the currently authenticated user.
    """
    raise HTTPException(status_code=501, detail="Not implemented")


class UserModel(BaseModel):
    color: str
    pronouns: list[str]


@router.patch("/users/update")
async def update_user(
    user: UserModel = Depends(authorize),
    db: Database = Depends(db.use),
) -> User:
    """
    Updates the specified authenticated user
    """
    user_data = User(**user)
    db.add(user_data)
    await db.commit()
    return user_data


# @router.delete("/users/delete")
# async def delete_user()


class LoginRequest(BaseModel):
    username: str
    password: str


@router.post("/login")
async def login(
    req: LoginRequest,
    db: Database = Depends(db.use),
) -> Session:
    """
    This function logs in a user and returns a session token.
    """
    user = (await db.exec(select(User).where(User.username == req.username))).first()
    if user is None or not verify_password(req.password, user.passhash):
        raise HTTPException(status_code=401, detail="Unauthorized")
    return new_session(db, user.username)


class RegisterRequest(BaseModel):
    username: str
    password: str


@router.post("/register")
async def register(
    req: RegisterRequest,
    db: Database = Depends(db.use),
) -> Session:
    """
    This function registers a new user and returns a session token.
    """
    raise HTTPException(status_code=501, detail="Not implemented")

    # async with db.begin_nested():
    #     user = User()
    #     db.add(user)
    #     await db.commit()
    #
    # userpw = UserPassword(id=user.id, passhash=hash_password(req.password))
    # db.add(userpw)
    # await db.commit()
    #
    # user = User(
    #     username=req.username,
    #     passhash=hash_password(req.password),
    # )
    # db.add(user)
    # return new_session(db, user.username)


@router.get("/groups/{group_id}")
async def get_group(
    group_id: int,
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> Group:
    """
    This function returns a group by ID.
    """
    # TODO: implement permission checking
    raise HTTPException(status_code=501, detail="Not implemented")


class GroupRequest(BaseModel):
    name: str
    bio: str


@router.post("/groups/create")
async def create_group(req: GroupRequest, db: Database = Depends(db.use)):
    # TODO: implement permissions checking
    group = Group(name=req.name, bio=req.bio)
    db.add(group)
    await db.commit()
    await db.refresh(group)
    return group


@router.delete("/groups/delete/{group_id}")
async def delete_group(group_id: int, db: Database = Depends(db.use)):
    # TODO: Make sure that the user has proper permissions to delete stuff
    query = select(Group).where(Group.id == group_id)
    group = (await db.exec(query)).one()
    await db.delete(group)
    await db.commit()
    return group


@router.patch("/groups/update/{group_id}")
async def update_group(
    group_id: int,
    req: GroupRequest,
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
):
    query = select(Group).where(Group.id == group_id)
    res = (await db.exec(query)).one()
    res.name = req.name
    res.bio = req.bio
    db.add(res)
    await db.commit()
    await db.refresh(res)
    return res


@router.get("/houses/{house_id}")
async def get_house(
    house_id: int,
    db: Database = Depends(db.use),
    me: str = Depends(authorize),
) -> House:
    """
    This function returns a house by ID.
    """
    # TODO: implement permission checking
    raise HTTPException(status_code=501, detail="Not implemented")


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
) -> StreamingResponse:
    """
    This function returns an asset by hash.
    """

    asset = (await db.exec(select(Asset).where(Asset.hash == asset_hash))).first()
    if asset is None:
        raise HTTPException(status_code=404, detail="Not found")

    stream = io.BytesIO(asset.data)
    return StreamingResponse(stream, media_type=asset.content_type)


class UploadFileResponse(BaseModel):
    hash: str
    content_type: str


@router.post("/assets")
async def upload_asset(
    file: UploadFile,
    db: Database = Depends(db.use),
    _: str = Depends(authorize),
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
    hash = base64.b64encode(hashlib.sha256(data).digest()).decode("utf-8")
    content_type = file.content_type

    asset = Asset(hash=hash, data=data, content_type=content_type)
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
