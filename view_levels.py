from db.models import *
from pydantic import BaseModel, Field
from typing import Union, Literal


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
    class PublicUser(PublicUser):
        level: Literal[AccessLevel.PUBLIC]

    class Level1User(Level1User):
        level: Literal[AccessLevel.LEVEL1]

    class Level2User(Level2User):
        level: Literal[AccessLevel.LEVEL2]

    class Level3User(Level3User):
        level: Literal[AccessLevel.LEVEL3]

    user: Union[PublicUser, Level1User, Level2User, Level3User] = Field(
        discriminator="level",
    )


if __name__ == "__main__":
    user: User = None  # type: ignore
    assert PublicUser(**user.model_dump())
    assert Level1User(**user.model_dump())
    assert Level2User(**user.model_dump())
    assert Level3User(**user.model_dump())
