
from job.api import upload
from job.api import test
from fastapi import APIRouter

app_router = APIRouter()

app_router.include_router(upload.router, prefix="/upload")
app_router.include_router(test.router, prefix="/test")
