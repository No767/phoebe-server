from dataclasses import dataclass
from typing import Annotated, AsyncGenerator, Optional
from fastapi import APIRouter, Depends, Form, HTTPException, Query
from sqlmodel import select
from haversine import haversine as calculate_distance, Unit as DistanceUnit
from api.groups import GroupResponse, group_response
from db import Database
from db.models import *
from utils.sessions import authorize
import db
import heapq


router = APIRouter(tags=["search"])


class SearchedGroup(GroupResponse):
    distance: float


@dataclass
class SearchParams:
    lat: float = Query(description="Latitude of the search point")
    lon: float = Query(description="Longitude of the search point")
    radius: float = Query(description="Radius of the search in the given unit")
    has_house: Optional[bool] = Query(None, description="Whether the group has a house")
    limit: int = Query(100, description="Maximum number of groups to return")
    unit: DistanceUnit = Query(
        default=DistanceUnit.MILES,
        description="Unit of the radius",
    )


async def search_nearest_groups(
    db: Database,
    params: SearchParams,
) -> list[tuple[Group, float]]:
    group_distances = [group async for group in generate_group_distances(db, params)]
    return heapq.nsmallest(params.limit, group_distances, key=lambda x: x[1])


async def generate_group_distances(
    db: Database,
    params: SearchParams,
) -> AsyncGenerator[tuple[Group, float], None]:
    query = select(Group).where(
        (Group.has_house == params.has_house if params.has_house is not None else True)
    )
    for group in await db.exec(query):
        distance = calculate_distance(
            (params.lat, params.lon),
            (group.lat, group.lon),
            unit=params.unit,
        )
        if distance <= params.radius:
            yield group, distance


@router.get("/search")
async def search_groups(
    params: SearchParams = Depends(),
    db: Database = Depends(db.use),
    me_id: int = Depends(authorize),
) -> list[SearchedGroup]:
    """
    Searches for groups within an given radius from an certain lat and lon point.
    """
    group_distances = await search_nearest_groups(db, params)
    group_responses = [
        (await group_response(group=group, me_id=me_id, db=db), distance)
        for group, distance in group_distances
    ]
    return [
        SearchedGroup(**group.model_dump(), distance=distance)
        for group, distance in group_responses
    ]
