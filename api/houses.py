from fastapi import APIRouter, Depends, HTTPException
from sqlmodel import select
from db import Database
from db.models import *
from sessions import authorize
import db


router = APIRouter(tags=["houses"])


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

    # raise HTTPException(status_code=501, detail="Not implemented")


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
