from db.models import *
from pydantic import BaseModel
from typing import Union


class Level1User(BaseModel):
    id: int
    color: str
    pronouns: list[str]


class Level2User(Level1User):
    bio: str


class UserView(BaseModel):
    level: int
    user: Union[Level1User, Level2User]
