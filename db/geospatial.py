from db import Database
from db.models import *
from sqlmodel import select
from haversine import haversine as calculate_distance
import haversine
import heapq


async def search_nearest_houses(
    db: Database,
    lat: float,
    lon: float,
    radius: float,  # in whatever unit the `unit` parameter is
    unit=haversine.Unit.MILES,
    limit=100,
) -> list[House]:
    heap = []

    for house in await db.exec(select(House)):
        distance = calculate_distance(
            (lat, lon),
            (house.lat, house.lon),
            unit=unit,
            normalize=True,
        )
        if distance <= radius:
            continue

        v = (-distance, house)
        if len(heap) < limit:
            heapq.heappush(heap, v)
        else:
            heapq.heappushpop(heap, v)

    return [house for _, house in heapq.nlargest(limit, heap)]
