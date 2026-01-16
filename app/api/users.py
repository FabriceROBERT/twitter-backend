from datetime import datetime, timedelta
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field
from app.schemas.schemas import UserProfile, UserUpdate
from app.services.users_service import get_current_user, get_user_by_id, get_user_followers_count, get_user_following_count, update_user


from app.db.database import get_db
from app.models.models import Bookmark, FacialExpression, Follow, Like, Retweet, Tweet, User

router = APIRouter()


# Schemas
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


@router.put("/me", response_model=UserResponse)
def update_profile(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mettre à jour son profil"""
    update_data = user_data.dict(exclude_unset=True)
    user = update_user(db, current_user.id, **update_data)
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    return user


@router.get("/{user_id}", response_model=UserProfile)
def get_user_profile(user_id: int, db: Session = Depends(get_db)):
    """Obtenir le profil d'un utilisateur"""
    user = get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    followers_count = get_user_followers_count(db, user_id)
    following_count = get_user_following_count(db, user_id)
    tweets_count = db.query(func.count(Tweet.id)).filter(Tweet.user_id == user_id).scalar()
    
    user = {
        "id": user.id,
        "email": user.email,
        "username": user.username,
        "firstname": user.firstname,
        "lastname": user.lastname,
        "bio": user.bio,
        "profile_image_url": user.profile_image_url,
        "banner_image_url": user.banner_image_url,
        "is_active": user.is_active,
        "followers_count": followers_count,
        "following_count": following_count,
        "tweets_count": tweets_count
    }
    
    return user

@router.get("/{user_id}/tweets")
def get_user_tweets(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Obtenir les tweets d'un utilisateur"""
    tweets = db.query(Tweet).filter(Tweet.user_id == user_id).order_by(desc(Tweet.created_at)).offset(offset).limit(limit).all()
    
    tweet_responses = []
    for tweet in tweets:
        is_liked = False
        is_retweeted = False
        is_bookmarked = False
        
        if current_user:
            is_liked = db.query(Like).filter(Like.user_id == current_user.id, Like.tweet_id == tweet.id).first() is not None
            is_retweeted = db.query(Retweet).filter(Retweet.user_id == current_user.id, Retweet.original_tweet_id == tweet.id).first() is not None
            is_bookmarked = db.query(Bookmark).filter(Bookmark.user_id == current_user.id, Bookmark.tweet_id == tweet.id).first() is not None
        
        tweet_responses.append({
            **tweet.__dict__,
            "author": tweet.user,
            "is_liked": is_liked,
            "is_retweeted": is_retweeted,
            "is_bookmarked": is_bookmarked
        })
    
    total_count = db.query(func.count(Tweet.id)).filter(Tweet.user_id == user_id).scalar()
    
    return {
        "tweets": tweet_responses,
        "total_count": total_count,
        "has_more": offset + limit < total_count
    }


@router.get("/{user_id}/followers")
def get_user_followers(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Obtenir les followers d'un utilisateur"""
    followers = db.query(User).join(Follow, Follow.follower_id == User.id).filter(Follow.following_id == user_id).offset(offset).limit(limit).all()
    
    total_count = db.query(func.count(Follow.id)).filter(Follow.following_id == user_id).scalar()
    
    return {
        "followers": followers,
        "total_count": total_count
    }

@router.get("/{user_id}/following")
def get_user_following(
    user_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """Obtenir les personnes suivies par un utilisateur"""
    following = db.query(User).join(Follow, Follow.following_id == User.id).filter(Follow.follower_id == user_id).offset(offset).limit(limit).all()

    total_count = db.query(func.count(Follow.id)).filter(Follow.follower_id == user_id).scalar()

    return {
        "following": following,
        "total_count": total_count
    }


@router.get("/suggestions/for-you")
def get_user_suggestions(
    limit: int = Query(5, ge=1, le=20),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user suggestions based on:
    - Users not yet followed
    - Similar emotional states (if facial recognition used)
    - Recent activity
    """
    # Get users already followed
    following_ids = db.query(Follow.following_id).filter(
        Follow.follower_id == current_user.id
    ).all()
    following_ids = [id[0] for id in following_ids]
    
    # Get current user's recent emotion
    recent_expression = (
        db.query(FacialExpression)
        .filter(FacialExpression.user_id == current_user.id)
        .filter(FacialExpression.created_at >= datetime.now() - timedelta(hours=24))
        .order_by(FacialExpression.created_at.desc())
        .first()
    )
    
    # Base query
    suggestions_query = db.query(User).filter(User.id != current_user.id)
    
    if following_ids:
        suggestions_query = suggestions_query.filter(User.id.notin_(following_ids))
    
    suggestions_query = suggestions_query.filter(User.is_active == True)
    
    # If user has recent emotion, prioritize users with similar emotions
    if recent_expression:
        user_emotion = recent_expression.emotion
        
        # Subquery to get users with similar recent emotions
        similar_emotion_users = (
            db.query(FacialExpression.user_id)
            .filter(FacialExpression.emotion == user_emotion)
            .filter(FacialExpression.created_at >= datetime.now() - timedelta(hours=24))
            .group_by(FacialExpression.user_id)
        )
        
        # Get suggestions with similar emotions first
        emotion_based_suggestions = (
            suggestions_query
            .filter(User.id.in_(similar_emotion_users))
            .order_by(desc(User.created_at))
            .limit(limit)
            .all()
        )
        
        # If not enough, fill with regular suggestions
        if len(emotion_based_suggestions) < limit:
            remaining = limit - len(emotion_based_suggestions)
            other_suggestions = (
                suggestions_query
                .filter(User.id.notin_([u.id for u in emotion_based_suggestions]))
                .order_by(desc(User.created_at))
                .limit(remaining)
                .all()
            )
            suggestions = emotion_based_suggestions + other_suggestions
        else:
            suggestions = emotion_based_suggestions
    else:
        # No emotion data, use regular suggestions
        suggestions = (
            suggestions_query
            .order_by(desc(User.created_at))
            .limit(limit)
            .all()
        )
    
    # Format response
    suggestions_response = []
    for user in suggestions:
        followers_count = get_user_followers_count(db, user.id)
        tweets_count = db.query(func.count(Tweet.id)).filter(
            Tweet.user_id == user.id
        ).scalar()
        
        # Get user's recent emotion if available
        user_emotion = (
            db.query(FacialExpression.emotion, FacialExpression.confidence)
            .filter(FacialExpression.user_id == user.id)
            .filter(FacialExpression.created_at >= datetime.now() - timedelta(hours=24))
            .order_by(FacialExpression.created_at.desc())
            .first()
        )
        
        suggestions_response.append({
            "id": user.id,
            "username": user.username,
            "firstname": user.firstname,
            "lastname": user.lastname,
            "bio": user.bio,
            "profile_image_url": user.profile_image_url,
            "followers_count": followers_count,
            "tweets_count": tweets_count,
            "current_mood": user_emotion[0] if user_emotion else None,
            "mood_confidence": user_emotion[1] if user_emotion else None,
        })
    
    return {
        "suggestions": suggestions_response,
        "total_count": len(suggestions_response),
        "filtered_by_emotion": recent_expression.emotion if recent_expression else None
    }