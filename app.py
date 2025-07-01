from fastapi import FastAPI, Request
from starlette.middleware.sessions import SessionMiddleware
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from database import engine, Base
from routes import auth_routes, ai_routes, main_routes
from ai_services.learning_service import learning_service

# This function creates and configures the FastAPI app
def create_app() -> FastAPI:
    # Initialize FastAPI app
    app = FastAPI(title="StudyMate")

    # Define a startup event to create database tables
    @app.on_event("startup")
    def on_startup():
        """Create database tables only after the app has started."""
        print("INFO:     Creating database tables...")
        Base.metadata.create_all(bind=engine)
        print("INFO:     Database tables created.")
        # Also initialize any services that need to run on startup
        learning_service.initialize()

        # Load the secret key for session management from the new config file
    from config import settings
    SECRET_KEY = settings.SECRET_KEY

    # Add session middleware to handle user sessions
    app.add_middleware(
        SessionMiddleware,
        secret_key=SECRET_KEY,
        max_age=3600  # Session expires after 1 hour (3600 seconds)
    )

    # Mount static files directory for CSS, JS, etc.
    app.mount("/static", StaticFiles(directory="static"), name="static")
    
    # Setup templates for rendering HTML
    templates = Jinja2Templates(directory="templates")

    # Include all the different API routers
    app.include_router(auth_routes.router)
    app.include_router(ai_routes.router)
    app.include_router(main_routes.router)

    # Define a root endpoint for the landing page
    @app.get("/", response_class=HTMLResponse, include_in_schema=False)
    async def root(request: Request):
        return templates.TemplateResponse("index.html", {"request": request})

    return app

# Create the app instance to be imported by Uvicorn
app = create_app()
