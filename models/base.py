from models.api.models import separate
from models.api.models import upsample
from models.api.models import speaker_id
from models.api import split
from models.api import compile
from fastapi import APIRouter

app_router = APIRouter()

app_router.include_router(
    speaker_id.router, prefix="/models/speaker-id", tags=["models"])
app_router.include_router(
    separate.router, prefix="/models/separate", tags=["models"])
app_router.include_router(
    upsample.router, prefix="/models/upsample", tags=["models"])
app_router.include_router(split.router, prefix="/split")
app_router.include_router(compile.router, prefix="/compile")
