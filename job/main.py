from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter, FastAPI
from ssl import SSLContext

from starlette.requests import Request
from starlette.responses import RedirectResponse

from job.base import app_router

def include_router(app):
    app.include_router(app_router)


def add_cors(app):
    origins = ["*"]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


def start_application():
    app = FastAPI(title="JOB API", description="This API contains task management processes and short tasks that can run asynchronously",
                  version=1.0, max_request_size=100 * 1024 * 1024, port=8000, host="0.0.0.0")
    include_router(app)
    add_cors(app)

    return app

app = start_application()

# @app.route('/{_:path}')
# async def https_redirect(request: Request):
#     return RedirectResponse(request.url.replace(scheme='https'))

