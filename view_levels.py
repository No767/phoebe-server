from db.models import *
from pydantic import BaseModel
from typing import Union


class PublicUser(BaseModel):
    id: int
    color: str
    pronouns: list[str]


class Level1User(PublicUser):
    bio: str


class Level2User(Level1User):
    pass


class Level3User(Level2User):
    pass


class UserView(BaseModel):
    level: int
    user: Union[PublicUser, Level1User, Level2User, Level3User]


if __name__ == "__main__":
    user: User = None  # type: ignore
    assert PublicUser(**user.model_dump())
    assert Level1User(**user.model_dump())
    assert Level2User(**user.model_dump())
    assert Level3User(**user.model_dump())
