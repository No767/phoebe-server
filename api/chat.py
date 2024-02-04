from fastapi import APIRouter, Depends, HTTPException, WebSocket
from sqlmodel import select, col
from pydantic import BaseModel, Field
from db import Database
from db.models import *
from utils.sessions import authorize
from typing import Sequence, Union
from api.assets import assert_asset_hash
import db
from viewlevels.group import assert_group_open_dms, group_level
from viewlevels.user import UserView, user_view_from_db
from sse_starlette.sse import EventSourceResponse, AsyncContentStream
from broadcaster import Broadcast
from datetime import datetime
import asyncio

router = APIRouter(tags=["chat"])

broadcast = Broadcast("memory://")


@router.get("/chat/groups")
async def get_chat_groups(
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> Sequence[Group]:
    """
    This function returns chat groups that the current user currently has an
    open DM with.
    """
    return (
        await db.exec(
            select(Group)
            .join(GroupRelationship)
            .where(
                GroupRelationship.user_id == me_id
                and GroupRelationship.open_dms == True
            )
        )
    ).all()


class ChatMessageResponse(BaseModel):
    id: int
    group_id: int
    author_id: int
    author: UserView
    content: ChatContent
    created_at: datetime


@router.get("/chat/groups/{group_id}/messages")
async def get_chat_messages(
    group_id: int,
    before_id: Optional[int] = None,
    limit: int = 50,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> Sequence[ChatMessageResponse]:
    """
    This function returns chat messages for a group that the current user is in.
    """
    assert assert_group_open_dms(db, me_id, group_id)

    if limit > 100:
        limit = 100

    messages_with_author = (
        await db.exec(
            select(ChatMessage, User)
            .join(User)
            .where(
                ChatMessage.group_id == group_id
                and User.id == ChatMessage.author_id
                and (ChatMessage.id < before_id if before_id is not None else True)
            )
            .order_by(col(ChatMessage.id).desc())
            .limit(limit)
        )
    ).all()
    level = await group_level(db, me_id, group_id)
    return [
        ChatMessageResponse(
            **message.model_dump(),
            author=await user_view_from_db(db, me_id, user.id),
        )
        for message, user in messages_with_author
    ]


class SendChatMessageRequest(BaseModel):
    content: ChatContent


@router.post("/chat/groups/{group_id}/messages")
async def send_chat_message(
    group_id: int,
    req: SendChatMessageRequest,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> ChatMessageResponse:
    """
    This function sends a chat message to a group.
    """
    await assert_group_open_dms(db, me_id, group_id)

    if isinstance(req.content, ChatContentSticker):
        await assert_asset_hash(db, req.content.asset_hash)
    if isinstance(req.content, ChatContentImage):
        await assert_asset_hash(db, req.content.asset_hash)

    await broadcast.publish(channel=str(group_id), message=req.content)
    message = ChatMessage(
        group_id=group_id,
        author_id=me_id,
        content=req.content,
    )

    db.add(message)
    await db.commit()
    await db.refresh(message)

    me = (await db.exec(select(User).where(User.id == me_id))).one()
    return ChatMessageResponse(
        **message.model_dump(),
        author=await user_view_from_db(db, me_id, me.id),
    )


@router.get("/chat/groups/{group_id}/messages/live")
async def live_chat_messages(
    group_id: int,
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> EventSourceResponse:
    async def ws_messages():
        async with broadcast.subscribe(channel=str(group_id)) as subscriber:
            async for event in subscriber:
                yield event

    await assert_group_open_dms(db, me_id, group_id)
    return EventSourceResponse(ws_messages())


async def assert_asset_hash(db: Database, hash: str):
    asset = (await db.exec(select(Asset.hash).where(Asset.hash == hash))).first()
    if asset is None:
        raise HTTPException(status_code=400, detail="Asset hash does not exist")
