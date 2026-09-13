from fastapi import APIRouter

from app.api.v1 import comparisons, payment_methods, search

router = APIRouter(prefix="/api/v1")
router.include_router(search.router)
router.include_router(comparisons.router)
router.include_router(payment_methods.router)
