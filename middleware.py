import secrets
import functools
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response, RedirectResponse
from database import SessionLocal
from models import User # Import User model

class SessionMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret_key: str = None):
        super().__init__(app)
        self.secret_key = secret_key or secrets.token_urlsafe(32)
        # In a real app, this should be a persistent store like Redis or a database
        self.sessions = {}

    async def dispatch(self, request: Request, call_next):
        session_id = request.cookies.get("session_id")
        request.state.session = {}
        request.state.user = None

        if session_id and session_id in self.sessions:
            request.state.session = self.sessions[session_id]
            if "user_id" in request.state.session:
                db = SessionLocal()
                try:
                    # Fetch user directly from the database
                    user = db.query(User).filter(User.id == request.state.session["user_id"]).first()
                    request.state.user = user
                finally:
                    db.close()

        response = await call_next(request)

        if getattr(request.state, 'session_modified', False):
            if not session_id or session_id not in self.sessions:
                session_id = secrets.token_urlsafe(32)
            self.sessions[session_id] = request.state.session
            response.set_cookie("session_id", session_id, httponly=True, max_age=86400 * 7) # 7 days

        return response

def login_required(func):
    """Decorator to require login for routes."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if not request or not getattr(request.state, "user", None):
            return RedirectResponse(url="/login", status_code=302)
        return await func(*args, **kwargs)
    return wrapper

def redirect_if_logged_in(func):
    """Decorator to redirect to dashboard if user is already logged in."""
    @functools.wraps(func)
    async def wrapper(*args, **kwargs):
        request = kwargs.get("request")
        if request and getattr(request.state, "user", None):
            return RedirectResponse(url="/dashboard", status_code=302)
        return await func(*args, **kwargs)
    return wrapper

def set_session(request: Request, key: str, value):
    """Helper to set session data."""
    request.state.session[key] = value
    request.state.session_modified = True

def get_session(request: Request, key: str, default=None):
    """Helper to get session data."""
    return request.state.session.get(key, default)

def clear_session(request: Request):
    """Helper to clear session."""
    request.state.session.clear()
    request.state.session_modified = True
