"""Root API router.

Aggregates every domain router under the shared /api prefix. This is a shared
contract between developers — add new domain routers here, agree on mount paths
with the other developer before changing existing ones.
"""

from fastapi import APIRouter

from app.api import business, customers, ml, opportunities, products, upload

api_router = APIRouter()

api_router.include_router(customers.router, prefix="/customers", tags=["customers"])
api_router.include_router(products.router, prefix="/products", tags=["products"])
api_router.include_router(business.router, prefix="/business", tags=["business"])
api_router.include_router(
    opportunities.router, prefix="/opportunities", tags=["opportunities"]
)
api_router.include_router(upload.router, prefix="/data", tags=["upload"])
api_router.include_router(ml.router, prefix="/ml", tags=["ml"])
