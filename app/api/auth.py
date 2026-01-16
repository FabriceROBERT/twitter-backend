# app/api/auth.py
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import timedelta
from pydantic import BaseModel, EmailStr, Field

from app.services.users_service import (
    authenticate_user, 
    create_user, 
    get_user_by_email, 
    get_user_by_username, 
    get_current_user
)
from app.db.database import get_db
from app.utils.security import create_access_token, ACCESS_TOKEN_EXPIRE_MINUTES
from app.models.models import User

router = APIRouter()


# ============ SCHEMAS ============

class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    firstname: str = Field(..., min_length=1, max_length=255)
    lastname: str = Field(..., min_length=1, max_length=255)


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    firstname: str
    lastname: str
    is_active: bool
    
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)



@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(user_data: UserRegister, db: Session = Depends(get_db)):
    """
    Register a new user
    
    - **email**: Valid email address
    - **username**: Unique username (3-50 characters)
    - **password**: Password (minimum 8 characters)
    - **firstname**: User's first name
    - **lastname**: User's last name
    """
    # Check if email already exists
    if get_user_by_email(db, user_data.email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Check if username already exists
    if get_user_by_username(db, user_data.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create user
    user = create_user(
        db,
        email=user_data.email,
        username=user_data.username,
        password=user_data.password,
        firstname=user_data.firstname,
        lastname=user_data.lastname
    )
    
    return user


@router.post("/login", response_model=Token)
def login(
    credentials: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Login with email and password
    
    - **email**: Your email address
    - **password**: Your password
    
    Returns access token for authentication
    """
    user = authenticate_user(db, credentials.email, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": str(user.id)},
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user
    }


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    """
    Get current user information
    
    Requires authentication token
    """
    return current_user


@router.post("/change-password")
def change_password(
    password_data: ChangePasswordRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change current user's password
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)
    """
    from app.services.users_service import change_user_password
    
    success = change_user_password(
        db,
        current_user.id,
        password_data.current_password,
        password_data.new_password
    )
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect"
        )
    
    return {"message": "Password changed successfully"}


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout (client should delete token)
    
    Note: JWT tokens are stateless, so logout is handled client-side
    by deleting the token. This endpoint exists for consistency.
    """
    return {"message": "Logged out successfully"}