from sqlmodel import Field, ARRAY, SQLModel, create_engine, Column, Float, String, JSON
from datetime import datetime
from typing import Optional


class UserPassword(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True, foreign_key="publicuser.id")
    passhash: str


class Session(SQLModel, table=True):
    token: str = Field(primary_key=True)
    user_id: Optional[int] = Field(foreign_key="publicuser.id")
    expires_at: datetime = Field(default_factory=datetime.utcnow)


class PublicUser(SQLModel, table=True):
    id: int = Field(primary_key=True)
    preferred_name: str
    # flairs: JSON
    pronouns: list[str] = Field(default=[], sa_column=Column(JSON))
    bio: str
    # gender: str
    group_id: Optional[int] = Field(default=None, foreign_key="group.id")


class Group(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    bio: str
    lat: float
    long: float
