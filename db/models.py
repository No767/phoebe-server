from sqlmodel import Field, ARRAY, SQLModel, create_engine, Column, Float, String, JSON
from datetime import datetime
from typing import Optional
from enum import Enum


class Session(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: Optional[int] = Field(foreign_key="user.id")
    expires_at: datetime = Field(default_factory=datetime.utcnow)


class User(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bio: str
    color: str
    gender: str
    preferred_name: str
    nickname: Optional[str] = None
    pronouns: list[str] = Field(default=[], sa_column=Column(JSON))
    sexual_orientations: list[str] = Field(default=[], sa_column=Column(JSON))
    group_id: Optional[int] = Field(default=None, foreign_key="group.id")


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
    house_id: Optional[int] = Field(foreign_key="house.id")


class House(SQLModel, table=True):
    """
    A house describes a living space for a group.
    Its location is roughly accurate to the nearest city.
    """

    id: Optional[int] = Field(default=None, primary_key=True)
    lat: float
    lon: float


class AccessLevel(int, Enum):
    PUBLIC = 0
    LEVEL1 = 1
    LEVEL2 = 2
    LEVEL3 = 3
