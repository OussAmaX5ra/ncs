from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware

from backend.api.endpoints.api_router import api_router
from backend.core.config import settings

# Create FastAPI backend
def create_application() -> FastAPI:
    middleware = [
        Middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)
    ]

    application = FastAPI(
        title="CodeFixer AI",
        description="AI-powered code debugging assistant",
        version="1.0.0",
        middleware=middleware
    )

    application.include_router(api_router, prefix="/api/v1")

    return application


app = create_application()

# Set all CORS enabled origins
if settings.BACKEND_CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[str(origin) for origin in settings.BACKEND_CORS_ORIGINS],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

# Add session middleware for OAuth
app.add_middleware(
    SessionMiddleware,
    secret_key=settings.SECRET_KEY,
    max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,  # Convert minutes to seconds
    same_site="lax",
    https_only=settings.ENVIRONMENT == "production"
)

# Include API router
app.include_router(api_router, prefix=settings.API_V1_STR)

@app.on_event("startup")
async def startup_event():
    """Setup OAuth providers on startup"""
    from backend.api.v1.endpoints.auth import setup_oauth
    setup_oauth()
    print("🚀 CodeFixer AI started with OAuth support")

@app.get("/")
async def root():
    return {
        "message": "Welcome to CodeFixer AI",
        "docs": "/docs",
        "api_v1": settings.API_V1_STR
    }

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:backend",
        host="0.0.0.0",
        port=8000,
        reload=True if settings.ENVIRONMENT == "development" else False
    )