"""
API Routers Package
"""

from app.routers.auth import router as auth_router
from app.routers.notices import router as notices_router

__all__ = ["auth_router", "notices_router"]

