from db import Database
from db.models import *
from sqlmodel import select


async def search_nearest_houses(
    db: Database,
    lat: float,
    lon: float,
    radius: float,
) -> list[House]:
    for house in await db.exec(select(House)):
        house
