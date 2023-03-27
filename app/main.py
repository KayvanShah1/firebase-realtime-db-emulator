from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.api import templates
from app.api.v1.api import api_router as api_v1_router
from app.api.v2.api import api_router as api_v2_router
from app.core import settings


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_PREFIX}/openapi.json",
    description="Firebase Realtime Database RestFul API Emulator",
)

# Handle CORS protection
origins = settings.BACKEND_CORS_ORIGINS

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# register all the APIRouter Endpoints
app.include_router(templates.router)
app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX, deprecated=True)
# app.include_router(api_v2_router, prefix=settings.API_V2_PREFIX, deprecated=True)
app.include_router(api_v2_router)

# Static Files and Templates
app.mount("/static", StaticFiles(directory=settings.STATIC_ROOT), name="static")
