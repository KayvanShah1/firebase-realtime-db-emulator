from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import templates
from app.api.v1.api import api_router as api_v1_router
from app.api.v2.api import api_router as api_v2_router
from app.core.settings import settings
from app.db.database import close_database, connect_database, is_database_configured


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None]:
    application_owns_database = not is_database_configured()
    if application_owns_database:
        mongodb_uri = settings.mongodb_uri.get_secret_value() if settings.mongodb_uri else None
        connect_database(mongodb_uri, settings.database_name)

    try:
        yield
    finally:
        if application_owns_database:
            close_database()


def create_app() -> FastAPI:
    application = FastAPI(
        title=settings.project_name,
        openapi_url="/openapi.json",
        description="Firebase Realtime Database RestFul API Emulator",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.backend_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(templates.router)
    application.include_router(api_v1_router, prefix=settings.api_v1_prefix, deprecated=True)
    application.include_router(api_v2_router)
    application.mount("/static", StaticFiles(directory=settings.static_root), name="static")
    return application


app = create_app()
