from api.models import separate
from api.models import upsample
from fastapi import APIRouter

app_router = APIRouter()

app_router.include_router(separate.router, prefix="/models/separate", tags=["models"])
app_router.include_router(upsample.router, prefix="/models/upsample", tags=["models"])