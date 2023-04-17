from typing import Optional
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter, FastAPI

from base import app_router


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
    app = FastAPI(title="ABCD-EDU API", description="ABCD-EDU",
                  version=1.0, max_request_size=100 * 1024 * 1024)
    include_router(app)
    add_cors(app)

    return app


app = start_application()
