from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.db.database import get_db
from app.models.models import Bookmark, Follow, Like, Reply, Retweet, Tweet, User
from app.schemas.schemas import TweetCreate, TweetResponse
from app.services.users_service import get_current_user

router = APIRouter()


@router.post("", response_model=TweetResponse, status_code=status.HTTP_201_CREATED)
def create_tweet(
    tweet_data: TweetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Créer un nouveau tweet"""
    tweet = Tweet(
        user_id=current_user.id,
        content=tweet_data.content,
        image_url=tweet_data.image_url,
        video_url=tweet_data.video_url
    )
    
    db.add(tweet)
    db.commit()
    db.refresh(tweet)
    
    return TweetResponse(
    id=tweet.id,
    user_id=tweet.user_id,
    content=tweet.content,
    image_url=tweet.image_url,
    video_url=tweet.video_url,
    created_at=tweet.created_at,
    updated_at=tweet.updated_at,
    likes_count=0,
    retweets_count=0,
    replies_count=0,
    author=current_user,
    hashtags=[],
    is_liked=False,
    is_retweeted=False,
    is_bookmarked=False
)


@router.get("/{tweet_id}", response_model=TweetResponse)
def get_tweet(
    tweet_id: int,
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Obtenir un tweet par ID"""
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    is_liked = False
    is_retweeted = False
    is_bookmarked = False
    
    if current_user:
        is_liked = db.query(Like).filter(Like.user_id == current_user.id, Like.tweet_id == tweet.id).first() is not None
        is_retweeted = db.query(Retweet).filter(Retweet.user_id == current_user.id, Retweet.original_tweet_id == tweet.id).first() is not None
        is_bookmarked = db.query(Bookmark).filter(Bookmark.user_id == current_user.id, Bookmark.tweet_id == tweet.id).first() is not None
    
    return {
        **tweet.__dict__,
        "author": tweet.user.username,
        "is_liked": is_liked,
        "is_retweeted": is_retweeted,
        "is_bookmarked": is_bookmarked
    }


# @router.get("", response_model=List[TweetResponse])
# def get_tweets(
#     limit: int = Query(20, ge=1, le=100),
#     offset: int = Query(0, ge=0),
#     db: Session = Depends(get_db),
#     current_user: Optional[User] = Depends(get_current_user)
# ):
#     """Obtenir la liste des tweets (timeline)"""

#     tweets = (
#         db.query(Tweet)
#         .order_by(desc(Tweet.created_at))
#         .offset(offset)
#         .limit(limit)
#         .all()
#     )

#     responses: List[TweetResponse] = []

#     for tweet in tweets:
#         is_liked = False
#         is_retweeted = False
#         is_bookmarked = False

#         if current_user:
#             is_liked = (
#                 db.query(Like)
#                 .filter(
#                     Like.user_id == current_user.id,
#                     Like.tweet_id == tweet.id
#                 )
#                 .first()
#                 is not None
#             )

#             is_retweeted = (
#                 db.query(Retweet)
#                 .filter(
#                     Retweet.user_id == current_user.id,
#                     Retweet.original_tweet_id == tweet.id
#                 )
#                 .first()
#                 is not None
#             )

#             is_bookmarked = (
#                 db.query(Bookmark)
#                 .filter(
#                     Bookmark.user_id == current_user.id,
#                     Bookmark.tweet_id == tweet.id
#                 )
#                 .first()
#                 is not None
#             )

#         responses.append(
#             TweetResponse(
#                 id=tweet.id,
#                 user_id=tweet.user_id,
#                 content=tweet.content,
#                 image_url=tweet.image_url,
#                 video_url=tweet.video_url,
#                 created_at=tweet.created_at,
#                 updated_at=tweet.updated_at,
#                 likes_count=tweet.likes_count,
#                 retweets_count=tweet.retweets_count,
#                 replies_count=tweet.replies_count,
#                 user=tweet.user,
#                 hashtags=[],
#                 is_liked=is_liked,
#                 is_retweeted=is_retweeted,
#                 is_bookmarked=is_bookmarked
#             )
#         )

#     return responses


@router.delete("/{tweet_id}")
def delete_tweet(
    tweet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprimer un tweet"""
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    if tweet.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this tweet")
    
    db.delete(tweet)
    db.commit()
    
    return {"message": "Tweet deleted successfully"}

@router.get("/{tweet_id}/replies")
def get_tweet_replies(
    tweet_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user)
):
    """Obtenir les réponses d'un tweet"""
    replies = db.query(Tweet).join(Reply, Reply.tweet_id == Tweet.id).filter(Reply.parent_tweet_id == tweet_id).order_by(desc(Tweet.created_at)).offset(offset).limit(limit).all()
    
    reply_responses = []
    for reply in replies:
        is_liked = False
        if current_user:
            is_liked = db.query(Like).filter(Like.user_id == current_user.id, Like.tweet_id == reply.id).first() is not None
        
        reply_responses.append({
            **reply.__dict__,
            "author": reply.user,
            "is_liked": is_liked
        })
    
    total_count = db.query(func.count(Reply.id)).filter(Reply.parent_tweet_id == tweet_id).scalar()
    
    return {
        "replies": reply_responses,
        "total_count": total_count
    }


@router.get("", response_model=list[TweetResponse])
def get_tweets(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    tweets = (
        db.query(Tweet)
        .order_by(desc(Tweet.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    response = []

    for tweet in tweets:
        is_liked = False
        is_retweeted = False
        is_bookmarked = False

        if current_user:
            is_liked = db.query(Like).filter_by(
                user_id=current_user.id, tweet_id=tweet.id
            ).first() is not None

            is_retweeted = db.query(Retweet).filter_by(
                user_id=current_user.id, original_tweet_id=tweet.id
            ).first() is not None

            is_bookmarked = db.query(Bookmark).filter_by(
                user_id=current_user.id, tweet_id=tweet.id
            ).first() is not None

        response.append(
            TweetResponse(
                id=tweet.id,
                user_id=tweet.user_id,
                content=tweet.content,
                image_url=tweet.image_url,
                video_url=tweet.video_url,
                created_at=tweet.created_at,
                updated_at=tweet.updated_at,
                likes_count=tweet.likes_count,
                retweets_count=tweet.retweets_count,
                replies_count=tweet.replies_count,
                author=tweet.user,
                hashtags=[],
                is_liked=is_liked,
                is_retweeted=is_retweeted,
                is_bookmarked=is_bookmarked,
            )
        )

    return response
