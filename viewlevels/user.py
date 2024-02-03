from db import Database
from db.models import *
from viewlevels.group import group_level
from pydantic import BaseModel, Field
from sqlmodel import select
from typing import Annotated, Union, Literal


class PublicUserData(BaseModel):
    id: int
    color: str
    avatar_hash: Optional[str]
    nickname: str
    pronouns: list[str]


class Level1UserData(PublicUserData):
    bio: str
    preferred_name: str
    genders: list[str]


class Level2UserData(Level1UserData):
    sexual_orientations: list[str]


class Level3UserData(Level2UserData):
    pass


class PublicUser(PublicUserData):
    access_level: Literal[AccessLevel.PUBLIC]


class Level1User(Level1UserData):
    access_level: Literal[AccessLevel.LEVEL1]


class Level2User(Level2UserData):
    access_level: Literal[AccessLevel.LEVEL2]


class Level3User(Level3UserData):
    access_level: Literal[AccessLevel.LEVEL3]


UserView = Annotated[
    Union[PublicUser, Level1User, Level2User, Level3User],
    Field(discriminator="access_level"),
]


def user_view(user: User, level: AccessLevel) -> UserView:
    match level:
        case AccessLevel.PUBLIC:
            view = PublicUser(access_level=level, **user.model_dump())
        case AccessLevel.LEVEL1:
            view = Level1User(access_level=level, **user.model_dump())
        case AccessLevel.LEVEL2:
            view = Level2User(access_level=level, **user.model_dump())
        case AccessLevel.LEVEL3:
            view = Level3User(access_level=level, **user.model_dump())
        case _:
            raise ValueError("Invalid access level")
    return view


async def user_view_from_db(db: Database, me_id: int, user: User) -> "UserView":
    """
    This function returns a UserView object, which is a view of a user's profile
    that is tailored to the current user's access level.
    """
    level = await group_level(db, me_id, user.group_id)
    return user_view(user, level)


if __name__ == "__main__":
    user: User = None  # type: ignore
    assert PublicUser(**user.model_dump())
    assert Level1User(**user.model_dump())
    assert Level2User(**user.model_dump())
    assert Level3User(**user.model_dump())
