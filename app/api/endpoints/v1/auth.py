import secrets
from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import RedirectResponse
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from authlib.integrations.starlette_client import OAuth

from app.web.core.config import settings
from app.web.core.security import create_access_token, get_password_hash
from app.web.db.session import get_db
from app.web.crud.user import user_crud
from app.web.schemas.auth import UserCreate, UserLogin, Token, UserResponse
from app.web.models.user import User
from app.web.dependencies.auth import get_current_user

router = APIRouter()

# OAuth setup
oauth = OAuth()


def setup_oauth():
    """Setup OAuth providers"""
    oauth.register(
        name='google',
        client_id=settings.GOOGLE_CLIENT_ID,
        client_secret=settings.GOOGLE_CLIENT_SECRET,
        access_token_url='https://oauth2.googleapis.com/token',
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        access_token_params=None,
        authorize_url='https://accounts.google.com/o/oauth2/auth',
        authorize_params=None,
        api_base_url='https://www.googleapis.com/oauth2/v1/',
        client_kwargs={
            'scope': 'openid email profile',
        }
    )


# Traditional auth endpoints
@router.post("/register", response_model=UserResponse)
def register(
        user_in: UserCreate,
        db: Session = Depends(get_db)
) -> Any:
    """Register new user with email and username validation"""
    # Check if email already exists
    existing_user = user_crud.get_by_email(db, email=user_in.email)
    if existing_user:
        raise HTTPException(
            status_code=400,
            detail="A user with this email already exists"
        )

    # Check if username already exists
    existing_username = user_crud.get_by_username(db, username=user_in.username)
    if existing_username:
        raise HTTPException(
            status_code=400,
            detail="A user with this username already exists"
        )

    # Validate password strength
    if len(user_in.password) < 8:
        raise HTTPException(
            status_code=400,
            detail="Password must be at least 8 characters long"
        )

    # Create new user
    user = user_crud.create(db, obj_in=user_in)
    return user


@router.post("/login", response_model=Token)
def login_for_access_token(
        db: Session = Depends(get_db),
        form_data: OAuth2PasswordRequestForm = Depends()
) -> Any:
    """OAuth2 compatible token login (supports email or username)"""
    # Try to authenticate with email first
    user = user_crud.authenticate(
        db, email=form_data.username, password=form_data.password
    )

    # If email auth fails, try username
    if not user:
        user = user_crud.authenticate_by_username(
            db, username=form_data.username, password=form_data.password
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    elif not user_crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.post("/login-json", response_model=Token)
def login_json(
        user_credentials: UserLogin,
        db: Session = Depends(get_db)
) -> Any:
    """JSON-based login (alternative to form-based login)"""
    # Try to authenticate with email first
    user = user_crud.authenticate(
        db, email=user_credentials.email_or_username, password=user_credentials.password
    )

    # If email auth fails, try username
    if not user:
        user = user_crud.authenticate_by_username(
            db, username=user_credentials.email_or_username, password=user_credentials.password
        )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email/username or password"
        )
    elif not user_crud.is_active(user):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )

    access_token = create_access_token(subject=user.id)
    return {
        "access_token": access_token,
        "token_type": "bearer",
    }


@router.get("/check-availability")
def check_availability(
        email: Optional[str] = None,
        username: Optional[str] = None,
        db: Session = Depends(get_db)
) -> Dict[str, bool]:
    """Check if email or username is available"""
    result = {}

    if email:
        existing_email = user_crud.get_by_email(db, email=email)
        result["email_available"] = existing_email is None

    if username:
        existing_username = user_crud.get_by_username(db, username=username)
        result["username_available"] = existing_username is None

    return result


@router.get("/me", response_model=UserResponse)
def read_users_me(
        current_user: User = Depends(get_current_user),
) -> Any:
    """Get current user"""
    return current_user


# OAuth endpoints
@router.get('/google-login')
async def google_login(request: Request):
    """Initiate Google OAuth login"""
    try:
        # Generate state for CSRF protection
        state = secrets.token_urlsafe(16)
        request.session['google_oauth_state'] = state

        # Generate nonce for ID token validation
        nonce = secrets.token_urlsafe(16)
        request.session['google_oauth_nonce'] = nonce

        # Create redirect URL
        redirect_uri = request.url_for('google_callback')

        return await oauth.google.authorize_redirect(
            request,
            redirect_uri,
            state=state,
            nonce=nonce
        )
    except Exception as e:
        print(f"❌ OAuth error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f'OAuth initialization failed: {str(e)}'
        )


@router.get('/google-callback')
async def google_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""

    # CSRF protection with state
    received_state = request.query_params.get('state')
    stored_state = request.session.pop('google_oauth_state', None)

    if received_state != stored_state:
        raise HTTPException(
            status_code=400,
            detail='Invalid state parameter. This could be a CSRF attack.'
        )

    try:
        # Get token from Google
        token = await oauth.google.authorize_access_token(request)

        # Get stored nonce and parse ID token with it
        nonce = request.session.pop('google_oauth_nonce', None)
        user_info = await oauth.google.parse_id_token(request, token, nonce=nonce)

        if not user_info:
            # Fallback to userinfo endpoint if ID token parsing fails
            resp = await oauth.google.get('userinfo', token=token)
            user_info = resp.json()

        google_id = user_info.get('sub') or user_info.get('id')
        email = user_info.get('email')
        username = user_info.get('name', email.split('@')[0] if email else 'user')

        if not email:
            raise HTTPException(status_code=400, detail="Email not provided by Google")

    except Exception as e:
        print("❌ Google login failed:", e)
        raise HTTPException(status_code=400, detail='Google login failed unexpectedly')

    # Find or create user
    user = user_crud.get_by_email(db, email=email)

    if not user:
        # Create new user with OAuth data
        user_create = UserCreate(
            email=email,
            username=username,
            password=secrets.token_hex(16),  # Random password for OAuth users
            google_id=google_id
        )
        user = user_crud.create(db, obj_in=user_create)
    else:
        # Update existing user with Google ID if not set
        if not user.google_id:
            user_crud.update(db, db_obj=user, obj_in={"google_id": google_id})

    # Create access token
    access_token = create_access_token(subject=user.id)

    # Store token in session for frontend
    request.session['access_token'] = access_token
    request.session['user_id'] = str(user.id)

    # Redirect to frontend with token
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?token={access_token}"
    return RedirectResponse(url=frontend_url, status_code=302)


@router.post('/logout')
async def logout(request: Request):
    """Log out user by clearing session"""
    request.session.clear()
    return {"message": "Logged out successfully"}