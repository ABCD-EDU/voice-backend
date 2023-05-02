from fastapi import APIRouter

from job.api import upload
from job.api import test
from job.api import file

app_router = APIRouter()

app_router.include_router(upload.router, prefix="/upload")
app_router.include_router(test.router, prefix="/test")
app_router.include_router(file.router, prefix="/file")
