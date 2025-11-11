"""Webhooks API Router"""

from fastapi import APIRouter
from api.v1.webhooks import ringcentral

router = APIRouter()

# Include webhook sub-routers
router.include_router(ringcentral.router)
