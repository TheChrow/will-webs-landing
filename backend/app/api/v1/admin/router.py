from fastapi import APIRouter

from app.api.v1.admin import auth, content, leads, legal

router = APIRouter(prefix="/admin")
router.include_router(auth.router)
router.include_router(content.router)
router.include_router(leads.router)
router.include_router(legal.router)
