from fastapi import APIRouter
from . import assets, chat, groups, me, search, users

router = APIRouter(prefix="/api")
for r in [assets, chat, groups, me, search, users]:
    router.include_router(r.router)
