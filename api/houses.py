from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from db import Database
from db.models import *
from sessions import authorize
import db
# from db.paginator import paginate_house
from db.geospatial import search_nearest_houses
from fastapi_pagination import Page
from fastapi_pagination.ext.async_sqlmodel import paginate
import haversine
from haversine import haversine as calculate_distance
import heapq
from fastapi_pagination.api import create_page
from fastapi_pagination.bases import AbstractParams
from fastapi_pagination.utils import verify_params

router = APIRouter(tags=["houses"])

async def look_for_houses(db: Database, params: Optional[AbstractParams], lat: float, lon: float, radius: float, unit=haversine.Unit.MILES, limit=100):
    params, raw_params = verify_params(params, "limit-offset")
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
            
    full_list = [house for _, house in heapq.nlargest(limit, heap)]
    
    return create_page(full_list, params=params)
class HouseRequest(BaseModel):
    lat: float
    lon: float


@router.get("/houses/{house_id}")
async def get_house(
    house_id: int,
    db: Database = Depends(db.use),
    # me: str = Depends(authorize),
) -> House:
    """
    This function returns a house by ID.
    """
    # TODO: implement permission checking
    query = select(House).where(House.id == house_id)
    house = (await db.exec(query)).one()
    return house




@router.get("/search")
async def search_houses(lat: float, lon: float, radius: float, limit: int = 100, db: Database = Depends(db.use)) -> Page[House]:
    """
    Searches for houses within an given radius from an certain lat and lon point.
    """
    return await look_for_houses(db, None, lat, lon, radius, haversine.Unit.MILES, 100)

@router.post("/houses")
async def create_house(req: HouseRequest, db: Database = Depends(db.use)) -> House:
    """
    Creates a new house
    """
    # TODO: assert that you don't already have a house
    house = House(**req.model_dump())
    db.add(house)
    await db.commit()
    await db.refresh(house)
    return house


@router.patch("/houses/{house_id}")
async def update_house(
    house_id: int, req: HouseRequest, db: Database = Depends(db.use)
) -> House:
    """
    Updates the information of a current house
    """
    query = select(House).where(House.id == house_id)
    house = (await db.exec(query)).one()
    house.lat = req.lat
    house.lon = req.lon
    db.add(house)
    await db.commit()
    await db.refresh(house)
    return house


@router.delete("/houses/{house_id}")
async def delete_house(house_id: int, db: Database = Depends(db.use)) -> House:
    """
    Deletes a house from the database
    """
    query = select(House).where(House.id == house_id)
    house = (await db.exec(query)).one()
    await db.delete(house)
    await db.commit()
    return house
