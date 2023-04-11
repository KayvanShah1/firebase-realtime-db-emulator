from fastapi import APIRouter

from app.api.v2.endpoints import retrieve_data, save_data, set_index

api_router = APIRouter()
api_router.include_router(save_data.router, tags=["Save Data"])
api_router.include_router(retrieve_data.router, tags=["Retrieve Data"])
api_router.include_router(set_index.router, tags=["Set Index"])
# api_router.include_router(login.router, tags=["Authentication"])
