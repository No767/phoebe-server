from sqlmodel import Relationship, SQLModel, Field
from datetime import datetime


class UserPassword(SQLModel, table=True):
    id: Optional[int] = Field(foreign_key="public_user.id")
    passhash: str


class Session(SQLModel, table=True):
    token: str = Field(primary_key=True)
    username: str = Field(foreign_key="user.username")
    expires_at: datetime = Field(default_factory=datetime.utcnow)
