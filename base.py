from api.models import separate
from api.models import upsample
from api.models import speaker_id
from api import upload
from api import split
from api import compile
from api import test
from fastapi import APIRouter

app_router = APIRouter()

app_router.include_router(
    speaker_id.router, prefix="/models/speaker-id", tags=["models"])
app_router.include_router(
    separate.router, prefix="/models/separate", tags=["models"])
app_router.include_router(
    upsample.router, prefix="/models/upsample", tags=["models"])
app_router.include_router(upload.router, prefix="/upload")
app_router.include_router(split.router, prefix="/split")
app_router.include_router(compile.router, prefix="/compile")
app_router.include_router(test.router, prefix="/test")
