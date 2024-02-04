#!/usr/bin/env python3

from dataclasses import dataclass
from faker import Faker
from db import Database
from db.models import *
from db.consts import PRONOUNS, GENDERS, SEXUAL_ORIENTATIONS
from api.me import RegisterRequest, register
from api.groups import CreateGroupRequest, create_group
from utils.assetutil import hash_bytes
from sqlmodel import select
import aiohttp
import random
import uvloop
import asyncio
import db as database
import argparse

N_USERS = 50
P_USER_WITH_GROUPS = 0.5
P_USER_WITH_AVATAR = 0.5
P_GROUP_WITH_HOUSE = 0.5


@dataclass
class CatAsset:
    data: bytes
    content_type: str


fake = Faker()
fake_cats: list[CatAsset] = []  # list of URLs

masculine_genders = [
    "male",
    "masculine",
    "transgender male",
]

feminine_genders = [
    "female",
    "feminine",
    "transgender female",
]

nonbinary_genders = [
    "non-binary",
    "agender",
]

misc_genders = [
    "androgynous",
    "bigender",
    "genderfluid",
    "genderqueer",
    "other",
]

assert all([g in GENDERS for g in masculine_genders])
assert all([g in GENDERS for g in feminine_genders])
assert all([g in GENDERS for g in nonbinary_genders])
assert all([g in GENDERS for g in misc_genders])


async def generate_one_user(i: int, db: Database):
    registration = random_registration()
    session = await register(registration, db)
    user_id = session.user_id

    print(f"Generated user with {registration.email=} and {registration.password=}")

    if roll(P_USER_WITH_AVATAR):
        cat_asset = random.choice(fake_cats)
        hash = hash_bytes(cat_asset.data)

        asset = (await db.exec(select(Asset.hash).where(Asset.hash == hash))).first()
        if asset is None:
            asset = Asset(
                hash=hash_bytes(cat_asset.data),
                data=cat_asset.data,
                content_type=cat_asset.content_type,
                alt="cat cat kitty cat",
            )
            db.add(asset)

        user = (await db.exec(select(User).where(User.id == user_id))).one()
        user.avatar_hash = hash
        db.add(user)

        await db.commit()

    if roll(P_USER_WITH_GROUPS):
        await create_group(random_group(), db=db, me_id=user_id)


def random_group() -> CreateGroupRequest:
    lat, lon = fake.latlng()
    return CreateGroupRequest(
        name=" ".join(fake.words(nb=2)),
        bio=fake.sentence(),
        color=fake.color(),
        lat=lat,
        lon=lon,
        has_house=roll(P_GROUP_WITH_HOUSE),
    )


def random_registration() -> RegisterRequest:
    pronoun = random.choice(PRONOUNS[:4])
    genders: list[str]
    preferred_name: str

    match pronoun:
        case "he/him":
            genders = [
                random.choice(masculine_genders),
                random.choice(masculine_genders + misc_genders),
            ]
            preferred_name = fake.name_male()
        case "she/her":
            genders = [
                random.choice(feminine_genders),
                random.choice(feminine_genders + misc_genders),
            ]
            preferred_name = fake.name_female()
        case "they/them" | "it/its":
            genders = [
                random.choice(nonbinary_genders),
                random.choice(nonbinary_genders + misc_genders),
            ]
            preferred_name = fake.name_nonbinary()
        case _:
            assert False

    return RegisterRequest(
        email=fake.email(),
        password=fake.password(),
        bio=fake.sentence(),
        color=fake.color(),
        preferred_name=preferred_name,
        nickname=fake.first_name_nonbinary(),
        genders=genders,
        pronouns=[pronoun, random.choice(PRONOUNS)],
        sexual_orientations=random.choices(SEXUAL_ORIENTATIONS, k=1),
    )


async def generate():

    await database.init_db()

    async with aiohttp.ClientSession() as http:
        CATS_URL = f"https://cataas.com/api/cats?size=square&limit={N_USERS}"
        async with http.get(CATS_URL) as resp:
            cats = await resp.json()
            cats = [cat["_id"] for cat in cats]

        async def cat_to_asset(id: str) -> CatAsset:
            async with http.get(f"https://cataas.com/cat/{id}") as resp:
                data = await resp.read()
                content_type = resp.headers["Content-Type"]
                return CatAsset(data, content_type)

        global fake_cats
        fake_cats = await asyncio.gather(*[cat_to_asset(cat) for cat in cats])

    async with database.get() as db:
        for i in range(N_USERS):
            await generate_one_user(i, db)


def roll(p) -> bool:
    return random.random() < p


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=str, default=":memory:")
    parser.add_argument("--seed", type=int, default=0)

    args = parser.parse_args()

    random.seed(args.seed)
    database.set_sqlite_path(args.database)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    uvloop.run(generate())
