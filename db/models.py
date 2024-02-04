from sqlmodel import (
    Field,
    SQLModel,
    Column,
    JSON,
)
from pydantic import BaseModel, field_validator
from datetime import datetime
from typing import Optional, Literal, Union
from enum import Enum
from utils import colors
from db.id import generate_id
from . import consts
from .id import generate_id
import math


class AccessLevel(int, Enum):
    """
    AccessLevel is an enumeration of the different access levels that a user can
    have.
    """

    PUBLIC = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3
    HIGHEST = LEVEL3


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

    user_id: int = Field(
        default_factory=generate_id,
        foreign_key="user.id",
        primary_key=True,
    )
    group_id: int = Field(
        default_factory=generate_id,
        foreign_key="group.id",
        primary_key=True,
    )
    level: AccessLevel
    open_dms: bool = Field(default=False)


class User(SQLModel, table=True):
    id: int = Field(default_factory=generate_id, primary_key=True)
    email: str = Field(unique=True)
    bio: str
    color: str
    avatar_hash: Optional[str] = Field(default=None, foreign_key="asset.hash")
    preferred_name: str
    nickname: str
    genders: list[str] = Field(default=[], sa_column=Column(JSON))
    pronouns: list[str] = Field(default=[], sa_column=Column(JSON))
    sexual_orientations: list[str] = Field(default=[], sa_column=Column(JSON))

    # group_id is the group that the user belongs to.
    group_id: Optional[int] = Field(default=None, foreign_key="group.id")

    # group_relationships is the relationships that the user has with other
    # groups.
    # group_relationships: list["Group"] = Relationship(link_model=GroupRelationship)

    @field_validator("genders")
    @classmethod
    def validate_genders(cls, genders: list[str]):
        for gender in genders:
            assert gender in consts.GENDERS

    @field_validator("pronouns")
    @classmethod
    def validate_pronouns(cls, pronouns: list[str]):
        for pronoun in pronouns:
            assert pronoun in consts.PRONOUNS

    @field_validator("sexual_orientations")
    @classmethod
    def validate_sexual_orientations(cls, sexual_orientations: list[str]):
        for sexual_orientation in sexual_orientations:
            assert sexual_orientation in consts.SEXUAL_ORIENTATIONS

    @field_validator("color")
    @classmethod
    def validate_color(cls, color: str):
        colors.assert_valid_color(color)


class UserPassword(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, foreign_key="user.id")
    passhash: str


class Group(SQLModel, table=True):
    """
    A group is a collection of users who live together.
    It is not necessarily a house (think group of partners needing a housemate).
    """

    id: int = Field(default_factory=generate_id, primary_key=True)
    name: str
    bio: str
    color: str
    icon_hash: Optional[str] = Field(default=None, foreign_key="asset.hash")

    lat: float
    lon: float
    has_house: bool = Field(default=False)

    @field_validator("color")
    @classmethod
    def validate_color(cls, color: str) -> str:
        colors.assert_valid_color(color)
        return color


class Asset(SQLModel, table=True):
    """
    An asset is any arbitrary binary data that can be stored in the database.
    It is identified by the base64-encoded SHA-256 hash of the data.
    Content types are supplied by the server.
    """

    hash: str = Field(primary_key=True)
    data: bytes
    created_at: datetime = Field(default_factory=datetime.utcnow)
    content_type: str
    alt: str | None = Field(default=None)


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
    id: int = Field(default_factory=generate_id, primary_key=True)

    # group_id is the origin group that the message was sent from.
    # When group_id is None, the group was deleted.
    group_id: int | None = Field(foreign_key="group.id")

    # author_id is the original author of the message.
    # The author will belong to the group.
    author_id: int | None = Field(foreign_key="user.id")

    # content is the message content.
    content: Union[ChatContentText, ChatContentSticker, ChatContentImage] = Field(
        discriminator="type",
        sa_column=Column(JSON),
    )
