from typing import Annotated, AsyncGenerator, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from haversine import haversine as calculate_distance, Unit as DistanceUnit
from db import Database
from db.models import *
from sessions import authorize
import db
import haversine
import heapq


router = APIRouter(tags=["search"])


class SearchedGroup(Group):
    distance: float


async def search_nearest_groups(
    db: Database,
    lat: float,
    lon: float,
    radius: Annotated[float, "Radius of the search in the given unit"],
    unit=DistanceUnit.MILES,
    limit=100,
    _: int = Depends(authorize),
) -> list[SearchedGroup]:
    group_distances = [
        group
        async for group in generate_group_distances(
            db,
            lat,
            lon,
            radius,
            unit=unit,
        )
    ]
    return heapq.nsmallest(limit, group_distances, key=lambda x: x.distance)


async def generate_group_distances(
    db: Database,
    lat: float,
    lon: float,
    radius: float,
    unit=DistanceUnit.MILES,
) -> AsyncGenerator[SearchedGroup, None]:
    for group in await db.exec(select(Group)):
        distance = calculate_distance(
            (lat, lon),
            (group.lat, group.lon),
            unit=unit,
        )
        if distance <= radius:
            yield SearchedGroup(**group.model_dump(), distance=distance)


@router.get("/search")
async def search_groups(
    lat: Annotated[float, "Latitude of the search point"],
    lon: Annotated[float, "Longitude of the search point"],
    radius: Annotated[float, "Radius of the search"],
    # has_house: Annotated[bool, "Whether the group has a house"] = True,
    unit=DistanceUnit.MILES,
    db: Database = Depends(db.use),
) -> list[SearchedGroup]:
    """
    Searches for groups within an given radius from an certain lat and lon point.
    """
    return await search_nearest_groups(
        db,
        lat,
        lon,
        radius,
        unit=unit,
        limit=200,
    )
