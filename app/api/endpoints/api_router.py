from app.api.endpoints.v1 import roadmap

api_router.include_router(roadmap.router, prefix="/roadmap", tags=["Roadmap Generator"])
