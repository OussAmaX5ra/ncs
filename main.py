from fastapi import FastAPI, Request
from starlette.responses import HTMLResponse
from starlette.staticfiles import StaticFiles
from starlette.templating import Jinja2Templates

from config import settings
from database import engine, Base
from middleware import SessionMiddleware
from routes import auth_routes, ai_routes, main_routes
from ai_services.learning_service import learning_service

app = FastAPI(title="StudyMate")

# Add session middleware with the secret key from settings
app.add_middleware(SessionMiddleware, secret_key=settings.SECRET_KEY)

@app.on_event("startup")
def on_startup():
    """Initialize services on application startup."""
    print("INFO:     Creating database tables if they do not exist...")
    Base.metadata.create_all(bind=engine)
    print("INFO:     Database tables checked/created.")
    learning_service.initialize()

# Mount static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Include application routers
app.include_router(auth_routes.router)
app.include_router(ai_routes.router)
app.include_router(main_routes.router)

@app.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    """Serve the main landing page."""
    return templates.TemplateResponse("index.html", {"request": request})

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
