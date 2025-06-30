from typing import Any, Dict, Optional, Union
from sqlalchemy.orm import Session
from app.web.core.security import get_password_hash, verify_password
from app.web.models.user import User
from app.web.schemas.auth import UserCreate, UserUpdate


class CRUDUser:
    def get(self, db: Session, id: int) -> Optional[User]:
        return db.query(User).filter(User.id == id).first()

    def get_by_email(self, db: Session, *, email: str) -> Optional[User]:
        return db.query(User).filter(User.email == email).first()

    def get_by_username(self, db: Session, *, username: str) -> Optional[User]:
        return db.query(User).filter(User.username == username).first()

    def get_by_google_id(self, db: Session, *, google_id: str) -> Optional[User]:
        return db.query(User).filter(User.google_id == google_id).first()

    def get_by_github_id(self, db: Session, *, github_id: str) -> Optional[User]:
        return db.query(User).filter(User.github_id == github_id).first()

    def get_by_discord_id(self, db: Session, *, discord_id: str) -> Optional[User]:
        return db.query(User).filter(User.discord_id == discord_id).first()

    def create(self, db: Session, *, obj_in: UserCreate) -> User:
        create_data = obj_in.dict()
        create_data.pop("password")
        db_obj = User(
            **create_data,
            hashed_password=get_password_hash(obj_in.password)
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def create_oauth_user(
            self,
            db: Session,
            *,
            email: str,
            username: str,
            full_name: Optional[str] = None,
            avatar_url: Optional[str] = None,
            google_id: Optional[str] = None,
            github_id: Optional[str] = None,
            discord_id: Optional[str] = None
    ) -> User:
        """Create user from OAuth provider"""
        import secrets

        # Generate random password for OAuth users
        random_password = secrets.token_hex(16)

        db_obj = User(
            email=email,
            username=username,
            full_name=full_name,
            avatar_url=avatar_url,
            hashed_password=get_password_hash(random_password),
            google_id=google_id,
            github_id=github_id,
            discord_id=discord_id,
            is_active=True
        )
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
            self, db: Session, *, db_obj: User, obj_in: Union[UserUpdate, Dict[str, Any]]
    ) -> User:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.dict(exclude_unset=True)

        if "password" in update_data:
            hashed_password = get_password_hash(update_data["password"])
            del update_data["password"]
            update_data["hashed_password"] = hashed_password

        for field in update_data:
            if hasattr(db_obj, field):
                setattr(db_obj, field, update_data[field])

        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def authenticate(self, db: Session, *, email: str, password: str) -> Optional[User]:
        user = self.get_by_email(db, email=email)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def authenticate_by_username(self, db: Session, *, username: str, password: str) -> Optional[User]:
        user = self.get_by_username(db, username=username)
        if not user:
            return None
        if not verify_password(password, user.hashed_password):
            return None
        return user

    def is_active(self, user: User) -> bool:
        return user.is_active

    def is_superuser(self, user: User) -> bool:
        return user.is_superuser

    def link_oauth_account(
            self,
            db: Session,
            *,
            user: User,
            provider: str,
            provider_id: str,
            avatar_url: Optional[str] = None
    ) -> User:
        """Link OAuth account to existing user"""
        update_data = {}

        if provider == "google":
            update_data["google_id"] = provider_id
        elif provider == "github":
            update_data["github_id"] = provider_id
        elif provider == "discord":
            update_data["discord_id"] = provider_id

        if avatar_url and not user.avatar_url:
            update_data["avatar_url"] = avatar_url

        return self.update(db, db_obj=user, obj_in=update_data)


user_crud = CRUDUser()