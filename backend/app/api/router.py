from fastapi import APIRouter

from app.api.health import router as health_router
from app.api.chat import router as chat_router
from app.api.crm import router as crm_router
from app.api.kb import router as kb_router

router = APIRouter()
router.include_router(health_router)
router.include_router(chat_router)
router.include_router(crm_router)
router.include_router(kb_router)
