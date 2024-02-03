from sqlmodel import Field, ARRAY, SQLModel, create_engine, Column, Float, String, JSON
from datetime import datetime
from typing import Optional


# class UserPassword(SQLModel, table=True):
#     # id: Optional[int] = Field(foreign_key="public_user.id")
#     passhash: str


class Session(SQLModel, table=True):
    token: str = Field(primary_key=True)
    username: str = Field(foreign_key="user.username")
    expires_at: datetime = Field(default_factory=datetime.utcnow)

class PublicUser(SQLModel, table=True):
    
    meta: dict = Field(default={}, sa_column=Column(JSON))
    
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
    
    
    
    
    
    # class Config:
    #     arbitary_types_allowed = True
    
    
    
    