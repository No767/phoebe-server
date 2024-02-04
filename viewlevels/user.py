from db import Database
from db.models import *
from viewlevels.group import group_level
from pydantic import BaseModel, Field
from sqlmodel import select
from typing import Annotated, Sequence, Union, Literal


class PublicUserData(BaseModel):
    id: int
    color: str
    avatar_hash: Optional[str]
    nickname: str
    pronouns: list[str]


class Level1UserData(PublicUserData):
    bio: str
    preferred_name: str
    photo_hashes: list[str]
    genders: list[str]


class Level2UserData(Level1UserData):
    sexual_orientations: list[str]
    group: Optional[Group]


class Level3UserData(Level2UserData):
    emergency_contacts: list[EmergencyContact]


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


def user_view(
    level: AccessLevel,
    user: User,
    group: Optional[Group],
    photos: Sequence[UserPhotos],
) -> UserView:
    # Start out with the most privileged view, then drill down to the more
    # public views by excluding fields.
    view = Level3User(
        **user.model_dump(),
        access_level=AccessLevel.LEVEL3,
        group=group,
        photo_hashes=[photo.hash for photo in photos],
    )

    if level <= AccessLevel.LEVEL2:
        view = Level2User(
            **view.model_dump(exclude={"access_level"}),
            access_level=AccessLevel.LEVEL2,
        )

    if level <= AccessLevel.LEVEL1:
        view = Level1User(
            **view.model_dump(exclude={"access_level"}),
            access_level=AccessLevel.LEVEL1,
        )

    if level <= AccessLevel.PUBLIC:
        view = PublicUser(
            **view.model_dump(exclude={"access_level"}),
            access_level=AccessLevel.PUBLIC,
        )

    return view


async def user_view_from_db(db: Database, me_id: int, user_id: int) -> "UserView":
    """
    This function returns a UserView object, which is a view of a user's profile
    that is tailored to the current user's access level.
    """
    user = await db.get_one(User, user_id)
    group = await db.get_one(Group, user.group_id) if user.group_id else None
    photos = (
        await db.exec(select(UserPhotos).where(UserPhotos.user_id == user_id))
    ).all()

    level = AccessLevel.PUBLIC
    if me_id == user_id:
        level = AccessLevel.HIGHEST
    elif group:
        level = await group_level(db, me_id, group.id)

    return user_view(level, user, group, photos)


if __name__ == "__main__":
    user: User = None  # type: ignore
    assert PublicUser(**user.model_dump())
    assert Level1User(**user.model_dump())
    assert Level2User(**user.model_dump())
    assert Level3User(**user.model_dump())
