from fastapi import APIRouter
from . import assets, chat, groups, me, search

router = APIRouter(prefix="/api")
for r in [assets, chat, groups, me, search]:
    router.include_router(r.router)
