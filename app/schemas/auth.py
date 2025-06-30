from typing import Optional
from pydantic import BaseModel, EmailStr, validator


# Shared properties
class UserBase(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    full_name: Optional[str] = None
    is_active: Optional[bool] = True
    is_superuser: bool = False


# Properties to receive via API on creation
class UserCreate(UserBase):
    email: EmailStr
    username: str
    password: str
    full_name: Optional[str] = None
    google_id: Optional[str] = None
    github_id: Optional[str] = None
    discord_id: Optional[str] = None

    # Add validation for username
    @validator('username')
    def validate_username(cls, v):
        if len(v) < 3:
            raise ValueError('Username must be at least 3 characters long')
        if len(v) > 20:
            raise ValueError('Username must be no more than 20 characters long')
        if not v.replace('_', '').replace('-', '').isalnum():
            raise ValueError('Username can only contain letters, numbers, hyphens, and underscores')
        return v.lower()  # Store usernames in lowercase for consistency

    # Add validation for password
    @validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        if len(v) > 128:
            raise ValueError('Password must be no more than 128 characters long')
        return v


# Properties to receive via API on update
class UserUpdate(UserBase):
    password: Optional[str] = None
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# Properties to return via API
class UserResponse(UserBase):
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    google_id: Optional[str] = None
    github_id: Optional[str] = None
    discord_id: Optional[str] = None

    class Config:
        orm_mode = True


# Properties stored in DB
class UserInDB(UserBase):
    id: int
    hashed_password: str

    class Config:
        orm_mode = True


# Login schemas
class UserLogin(BaseModel):
    email_or_username: str  # Can be either email or username
    password: str

class UserLoginEmail(BaseModel):
    email: EmailStr
    password: str

class UserLoginUsername(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class TokenPayload(BaseModel):
    sub: Optional[int] = None


# OAuth specific schemas
class OAuthUserInfo(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    provider_id: str
    provider: str  # "google", "github", "discord"


class GoogleUserInfo(BaseModel):
    sub: str
    email: EmailStr
    name: Optional[str] = None
    picture: Optional[str] = None
    email_verified: Optional[bool] = None


class GitHubUserInfo(BaseModel):
    id: int
    login: str
    email: Optional[EmailStr] = None
    name: Optional[str] = None
    avatar_url: Optional[str] = None


class DiscordUserInfo(BaseModel):
    id: str
    username: str
    email: Optional[EmailStr] = None
    avatar: Optional[str] = None
    discriminator: str

# Availability check schemas
class AvailabilityCheck(BaseModel):
    email_available: Optional[bool] = None
    username_available: Optional[bool] = None

# Password reset schemas (for future use)
class PasswordResetRequest(BaseModel):
    email: EmailStr

class PasswordReset(BaseModel):
    token: str
    new_password: str

    @validator('new_password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters long')
        return v