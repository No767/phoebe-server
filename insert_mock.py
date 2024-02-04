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
from urllib.parse import urlencode
import aiohttp
import random
import uvloop
import asyncio
import db as database
import argparse
from global_land_mask import globe

N_USERS = 40
P_USER_WITH_GROUPS = 0.5
P_USER_WITH_AVATAR = 0.5
P_GROUP_WITH_HOUSE = 0.5

N_CATS_SQUARE = 70
N_CATS = 70


@dataclass
class CatAsset:
    data: bytes
    content_type: str


fake = Faker()
fake_cats: list[CatAsset] = []
fake_cats_square: list[CatAsset] = []

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
    "bigender",
    "intersex",
    "pangender",
]

misc_genders = [
    "androgyne",
    "altersex",
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
    assert user_id is not None

    print(f"Generated user with {registration.email=} and {registration.password=}")

    if roll(P_USER_WITH_AVATAR):
        cat_asset = fake_cats_square[i % len(fake_cats_square)]
        hash = await ensure_asset(cat_asset.data, cat_asset.content_type, db)
        user = (await db.exec(select(User).where(User.id == user_id))).one()
        user.avatar_hash = hash
        db.add(user)
        await db.commit()
        print(f"Generated avatar for above user")

    photo_attempts = 0
    photo_hashes: set[str] = set()
    n_photos_wanted = random.randint(0, 11)
    while len(photo_hashes) < n_photos_wanted and photo_attempts < 1000:
        photo_attempts += 1
        cat_asset = random.choice(fake_cats)
        photo_hash = await ensure_asset(cat_asset.data, cat_asset.content_type, db)
        if photo_hash in photo_hashes:
            continue
        photo = UserPhoto(user_id=user_id, photo_hash=photo_hash)
        photo_hashes.add(photo_hash)
        db.add(photo)
    await db.commit()
    print(f"Generated {len(photo_hashes)} photo roll for above user")

    if roll(P_USER_WITH_GROUPS):
        cat_asset = random.choice(fake_cats_square)

        group = random_group()
        group.icon_hash = await ensure_asset(cat_asset.data, cat_asset.content_type, db)

        await create_group(group, db=db, me_id=user_id)
        print(f"Generated group for above user")


def random_group() -> CreateGroupRequest:
    def _gen_points(origin_lat: float, origin_lon: float):
        DEV = 0.1  # deviation

        lat = origin_lat + random.uniform(-DEV, +DEV)
        lon = origin_lon + random.uniform(-DEV, +DEV)
        return (lat, lon)

    # UCLA Powell Library
    lat, lon = _gen_points(34.07181475768593, -118.44212446579002)

    while not globe.is_land(lat, lon):
        lat, lon = _gen_points(lat, lon)

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

    genders = list(set(genders))
    pronouns = list(set([pronoun, random.choice(PRONOUNS)]))

    return RegisterRequest(
        email=fake.email(),
        password=fake.password(),
        bio=fake.sentence(),
        color=fake.color(),
        preferred_name=preferred_name,
        nickname=fake.first_name_nonbinary(),
        genders=genders,
        pronouns=pronouns,
        sexual_orientations=random.choices(SEXUAL_ORIENTATIONS, k=1),
    )


async def generate():
    await database.init_db()

    async with aiohttp.ClientSession() as http:
        cats_square = await list_cat_ids(http, {"size": "square"}, N_CATS_SQUARE)
        print(f"Got {len(cats_square)} square cats")

        cats = await list_cat_ids(http, {}, N_CATS)
        print(f"Got {len(cats)} cats")

        async def cat_to_asset(id: str) -> CatAsset:
            while True:
                async with http.get(f"https://cataas.com/cat/{id}") as resp:
                    if resp.status != 200:
                        # probably rate limited, retry in a bit
                        await asyncio.sleep(0.5)
                        continue

                    data = await resp.read()
                    content_type = resp.headers["Content-Type"]
                    print(f"Downloaded cat {id}")
                    return CatAsset(data, content_type)

        async def cats_to_assets(ids: list[str]) -> list[CatAsset]:
            print(f"Downloading {len(ids)} cats")
            # return await asyncio.gather(*[cat_to_asset(id) for id in ids])
            return [await cat_to_asset(id) for id in ids]

        global fake_cats_square
        global fake_cats

        fake_cats_square = await cats_to_assets(cats_square)
        fake_cats = await cats_to_assets(cats)

    async with database.get() as db:
        for i in range(N_USERS):
            await generate_one_user(i, db)


async def list_cat_ids(http: aiohttp.ClientSession, query={}, limit=100) -> list[str]:
    ids: list[str] = []
    skip = 0
    while len(ids) < limit:
        query["skip"] = skip
        q = urlencode(query)
        u = f"https://cataas.com/api/cats?{q}"
        async with http.get(u) as resp:
            cats = await resp.json()
            ids.extend([cat["_id"] for cat in cats])
        skip += len(cats)
    ids = ids[:limit]
    return ids


async def ensure_asset(
    data: bytes, content_type: str, db: Database, alt="cat cat kitty cat"
) -> str:
    hash = hash_bytes(data)
    asset = await db.get(Asset, hash)
    if asset is None:
        asset = Asset(
            hash=hash,
            data=data,
            content_type=content_type,
            alt=alt,
        )
        db.add(asset)
        await db.commit()
    return hash


def roll(p) -> bool:
    return random.random() <= p


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=str, default=":memory:")
    parser.add_argument("--seed", type=int, default=38474)

    args = parser.parse_args()

    random.seed(args.seed)
    database.set_sqlite_path(args.database)

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
    uvloop.run(generate())
