from fastapi import APIRouter
from . import assets, chat, groups, houses, me, search

router = APIRouter(prefix="/api")
for r in [assets, chat, groups, houses, me, search]:
    router.include_router(r.router)
