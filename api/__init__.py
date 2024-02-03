from fastapi import APIRouter
from . import assets, chat, groups, houses, me

router = APIRouter(prefix="/api")
for r in [assets, chat, groups, houses, me]:
    router.include_router(r.router)
