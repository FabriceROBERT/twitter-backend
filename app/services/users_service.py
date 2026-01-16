from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer


from app.models.models import User, Follow
from app.utils.security import get_password_hash, verify_password, decode_token
from app.db.database import get_db


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


# USER CRUD 

def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    return db.query(User).filter(User.id == user_id).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    return db.query(User).filter(User.email == email).first()


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    return db.query(User).filter(User.username == username).first()


def create_user(
    db: Session,
    email: str,
    username: str,
    password: str,
    firstname: str,
    lastname: str
) -> User:
    hashed_password = get_password_hash(password)
    
    db_user = User(
        email=email,
        username=username,
        password=hashed_password,
        firstname=firstname,
        lastname=lastname
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user


def authenticate_user(db: Session, email: str, password: str) -> Optional[User]:
    user = get_user_by_email(db, email)
    if not user:
        return None
    
    if not verify_password(password, user.password):
        return None
    
    if not user.is_active:
        return None
    
    return user


def change_user_password(
    db: Session,
    user_id: int,
    current_password: str,
    new_password: str
) -> bool:
    """Change user password for future functionnalities """
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    # Verify current password
    if not verify_password(current_password, user.password):
        return False
    
    # Set new password
    user.password = get_password_hash(new_password)
    db.commit()
    
    return True


def update_user(db: Session, user_id: int, **kwargs) -> Optional[User]:
    """Update user fields"""
    user = get_user_by_id(db, user_id)
    if not user:
        return None
    
    kwargs.pop('password', None)
    kwargs.pop('id', None)
    
    for key, value in kwargs.items():
        if hasattr(user, key) and value is not None:
            setattr(user, key, value)
    
    db.commit()
    db.refresh(user)
    return user


def delete_user(db: Session, user_id: int) -> bool:
    user = get_user_by_id(db, user_id)
    if not user:
        return False
    
    user.is_active = False
    db.commit()
    return True


# AUTHENTICATION DEPENDENCY

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    try:
        payload = decode_token(token)
        user_id = payload.get("sub")
        if user_id is None:
            raise credentials_exception
    except Exception:
        raise credentials_exception
    
    user = get_user_by_id(db, user_id=int(user_id))
    if user is None:
        raise credentials_exception
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Inactive user"
        )
    
    return user

# USER STATS

def get_user_followers_count(db: Session, user_id: int) -> int:
    """Get number of followers"""
    return db.query(func.count(Follow.id)).filter(
        Follow.following_id == user_id
    ).scalar() or 0


def get_user_following_count(db: Session, user_id: int) -> int:
    """Get number of users being followed"""
    return db.query(func.count(Follow.id)).filter(
        Follow.follower_id == user_id
    ).scalar() or 0