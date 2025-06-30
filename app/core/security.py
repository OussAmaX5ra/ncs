import bcrypt
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_
from app.web.models.user import User


def hash_password(password: str) -> str:
    """Hash a password using bcrypt."""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash."""
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def authenticate_user(db: Session, username_or_email: str, password: str) -> Optional[User]:
    """Authenticate user against the database."""
    user = db.query(User).filter(
        or_(
            User.username == username_or_email.lower(),
            User.email == username_or_email.lower()
        )
    ).first()

    if not user or not verify_password(password, user.password):
        return None

    return user