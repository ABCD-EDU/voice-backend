from api.models import separate
from api.models import upsample
from api import upload
from api import split
from fastapi import APIRouter

app_router = APIRouter()

app_router.include_router(
    separate.router, prefix="/models/separate", tags=["models"])
app_router.include_router(
    upsample.router, prefix="/models/upsample", tags=["models"])
app_router.include_router(upload.router, prefix="/upload")
app_router.include_router(split.router, prefix="/split")
