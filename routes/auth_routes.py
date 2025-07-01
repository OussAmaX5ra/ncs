from fastapi import APIRouter, Request, Depends, Form, status
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from sqlalchemy.orm import Session
from database import get_db
from models import User
from auth import get_password_hash, verify_password
from middleware import set_session, clear_session, redirect_if_logged_in
import logging

log = logging.getLogger(__name__)

router = APIRouter()
templates = Jinja2Templates(directory="templates")

# --- Signup Routes ---

@router.get("/signup", response_class=HTMLResponse)
@redirect_if_logged_in
async def get_signup_form(request: Request):
    log.debug("Accessed signup page route")
    """Displays the signup form."""
    return templates.TemplateResponse("signup.html", {"request": request})

@router.post("/signup")
async def handle_signup(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    email: str = Form(...),
    password: str = Form(...),
    confirm_password: str = Form(...)
):
    log.debug(f"Accessed handle_signup with username: {username}")
    """Handles the signup form submission."""
    # 1. Check if passwords match
    if password != confirm_password:
        log.warning("Signup failed: Passwords do not match.")
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Passwords do not match"})

    # 2. Check if user already exists
    if db.query(User).filter(User.email == email).first():
        log.warning(f"Signup failed: Email '{email}' already registered.")
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Email already registered"})
    if db.query(User).filter(User.username == username).first():
        log.warning(f"Signup failed: Username '{username}' already taken.")
        return templates.TemplateResponse("signup.html", {"request": request, "error": "Username already taken"})

    # 3. Create new user
    log.info(f"Validation passed. Creating new user '{username}'.")
    new_user = User(
        username=username,
        email=email,
        password_hash=get_password_hash(password)
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # 4. Redirect to login page with a success message
    log.info(f"User '{username}' created successfully. Redirecting to login page.")
    return RedirectResponse(url="/login?message=Signup successful. Please log in.", status_code=status.HTTP_303_SEE_OTHER)

# --- Login / Logout Routes ---

@router.get("/login", response_class=HTMLResponse)
@redirect_if_logged_in
async def get_login_form(request: Request, message: str = None):
    log.debug("Accessed login page route")
    """Displays the login form."""
    context = {"request": request}
    if message:
        context["message"] = message
        log.info(f"Displaying message on login page: {message}")
    return templates.TemplateResponse("login.html", context)

@router.post("/login")
async def handle_login(
    request: Request,
    db: Session = Depends(get_db),
    username: str = Form(...),
    password: str = Form(...)
):
    log.debug(f"Accessed handle_login with username: {username}")
    """Handles the login form submission."""
    user = db.query(User).filter(User.username == username).first()

    if not user:
        log.warning(f"Login failed: Username '{username}' not found.")
        return templates.TemplateResponse("login.html", {"request": request, "error": f"Username '{username}' not found."})

    if not verify_password(password, user.password_hash):
        log.warning(f"Login failed: Incorrect password for username '{username}'.")
        return templates.TemplateResponse("login.html", {"request": request, "error": "Incorrect password. Please try again."})


    set_session(request, "user_id", str(user.id))
    return RedirectResponse(url="/dashboard", status_code=status.HTTP_303_SEE_OTHER)

@router.get("/logout")
async def logout(request: Request):
    log.debug("Accessed logout route")
    """Logs the user out and redirects to the login page."""
    clear_session(request)
    return RedirectResponse(url="/login", status_code=status.HTTP_303_SEE_OTHER)