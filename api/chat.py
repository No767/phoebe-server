from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from pydantic import BaseModel, Field
from db import Database
from db.models import *
from sessions import authorize
from typing import Union
from api.assets import assert_asset_hash
import db

router = APIRouter(tags=["chat"])


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
