from passlib.context import CryptContext

# Create a password context for hashing and verifying passwords
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def get_password_hash(password: str) -> str:
    """Hashes a password using bcrypt."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)
import hashlib
import secrets
from typing import Optional
from uuid import UUID

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from models import User
from database import get_db

class AuthService:
    @staticmethod
    def hash_password(password: str) -> str:
        """Hashes a password with a salt using SHA-256."""
        salt = secrets.token_hex(16)
        password_hash = hashlib.sha256((password + salt).encode()).hexdigest()
        return f"{salt}:{password_hash}"

    @staticmethod
    def verify_password(password: str, hashed_password: str) -> bool:
        """Verifies a password against its stored hash."""
        try:
            salt, stored_hash = hashed_password.split(':')
            return hashlib.sha256((password + salt).encode()).hexdigest() == stored_hash
        except (ValueError, AttributeError):
            return False

    @staticmethod
    def create_user(db: Session, username: str, email: str, password: str) -> Optional[User]:
        """Create a new user, returns None if user already exists."""
        if db.query(User).filter((User.username == username) | (User.email == email)).first():
            return None
        
        hashed_password = AuthService.hash_password(password)
        user = User(username=username, email=email, password_hash=hashed_password)
        
        db.add(user)
        db.commit()
        db.refresh(user)
        return user

    @staticmethod
    def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
        """Authenticates a user by username/email and password."""
        user = db.query(User).filter(
            (User.username == username_or_email) | (User.email == username_or_email)
        ).first()
        if user and AuthService.verify_password(password, user.password_hash):
            return user
        return None

    @staticmethod
    def get_user_by_id(db: Session, user_id: UUID) -> Optional[User]:
        """Retrieves a user by their ID."""
        return db.query(User).filter(User.id == user_id).first()


# --- FastAPI Dependencies for Route Protection ---

async def get_current_user(request: Request, db: Session = Depends(get_db)) -> Optional[User]:
    """
    Dependency to get the current user from the session cookie.
    """
    user_id = request.state.session.get("user_id")
    if not user_id:
        return None
    
    try:
        user_uuid = UUID(user_id)
    except ValueError:
        return None
        
    user = AuthService.get_user_by_id(db, user_uuid)
    return user

async def get_current_active_user(current_user: Optional[User] = Depends(get_current_user)) -> User:
    """
    Dependency to get the current active user.
    If the user is not logged in or inactive, it raises an HTTPException.
    This is the function to be used in protected API routes.
    """
    if not current_user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated. Please log in.",
        )
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="Inactive user.")
    
    return current_user
