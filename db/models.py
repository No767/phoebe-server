from sqlmodel import (
    Field,
    SQLModel,
    Column,
    JSON,
    Relationship,
)
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, Literal, Union
from enum import Enum


class AccessLevel(int, Enum):
    """
    AccessLevel is an enumeration of the different access levels that a user can
    have.
    """

    PUBLIC = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3


class Session(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id")
    expires_at: datetime = Field(default_factory=datetime.utcnow)


class GroupRelationship(SQLModel, table=True):
    """
    A group relationship describes the relationship between a user outside of a
    group and a group. If the user is inside the group, then this relationship
    is not used, and the highest access level is implied.
    """

    user_id: Optional[int] = Field(
        default=None,
        foreign_key="user.id",
        primary_key=True,
    )
    group_id: Optional[int] = Field(
        default=None,
        foreign_key="group.id",
        primary_key=True,
    )
    level: AccessLevel
    open_dms: bool = Field(default=False)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bio: str
    color: str
    gender: str
    preferred_name: str
    nickname: Optional[str] = None
    pronouns: list[str] = Field(default=[], sa_column=Column(JSON))
    sexual_orientations: list[str] = Field(default=[], sa_column=Column(JSON))

    # group_id is the group that the user belongs to.
    group_id: Optional[int] = Field(default=None, foreign_key="group.id")
    group: Optional["Group"] = Relationship(back_populates="people")

    # group_relationships is the relationships that the user has with other
    # groups.
    group_relationships: list["Group"] = Relationship(link_model=GroupRelationship)


class UserPassword(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, foreign_key="user.id")
    passhash: str


class Group(SQLModel, table=True):
    """
    A group is a collection of users who live together.
    It is not necessarily a house (think group of partners needing a housemate).
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    bio: str
    users: list[User] = Relationship(back_populates="group")
    house_id: Optional[int] = Field(foreign_key="house.id")
    house: Optional["House"] = Relationship(back_populates="group")


class House(SQLModel, table=True):
    """
    A house describes a living space for a group.
    Its location is roughly accurate to the nearest city.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    lat: float
    lon: float
    group: Optional[Group] = Relationship(back_populates="house")


class Asset(SQLModel, table=True):
    """
    An asset is any arbitrary binary data that can be stored in the database.
    It is identified by the base64-encoded SHA-256 hash of the data.
    Content types are supplied by the server.
    """

    hash: str = Field(primary_key=True)
    data: bytes
    content_type: str


class ChatContentText(BaseModel):
    """
    A message that contains Markdown text.
    """

    type: Literal["text"]
    markdown: str


class ChatContentSticker(BaseModel):
    """
    A message that contains a single sticker.
    """

    type: Literal["sticker"]
    asset_hash: str


class ChatContentImage(BaseModel):
    """
    A message that contains a single image.
    """

    type: Literal["image"]
    asset_hash: str


class ChatMessage(SQLModel, table=True):
    # id is the unique identifier for the message.
    # It is defined as a Snowflake ID and therefore also contains a timestamp.
    id: int = Field(primary_key=True)

    # group_id is the origin group that the message was sent from.
    # When group_id is None, the group was deleted.
    group_id: int | None = Field(foreign_key="group.id")
    group: Optional[Group] = Relationship()

    # author_id is the original author of the message.
    # The author will belong to the group.
    author_id: int | None = Field(foreign_key="user.id")
    author: Optional[User] = Relationship()

    # content is the message content.
    content: Union[ChatContentText, ChatContentSticker, ChatContentImage] = Field(
        discriminator="type",
        sa_column=Column(JSON),
    )
