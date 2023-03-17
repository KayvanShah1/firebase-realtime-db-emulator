from fastapi import APIRouter

from app.api.v1.endpoints import firebase

api_router = APIRouter()
api_router.include_router(firebase.router, tags=["Firebase"])
# api_router.include_router(blog.router, prefix="/blogs", tags=["Blogs"])
# api_router.include_router(login.router, tags=["Authentication"])
