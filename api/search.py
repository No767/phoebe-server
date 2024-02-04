from fastapi import APIRouter, Depends
from db import Database, geospatial
from db.models import House
from db.geospatial import search_nearest_houses
import db

router = APIRouter(tags=["search"])


@router.get("/search")
async def search_houses(
    lat: float,
    lon: float,
    radius: float,
    db: Database = Depends(db.use),
) -> list[House]:
    """
    Searches for houses within an given radius from an certain lat and lon point.
    """
    return await search_nearest_houses(
        db,
        lat,
        lon,
        radius,
        geospatial.Unit.MILES,
        limit=200,
    )
