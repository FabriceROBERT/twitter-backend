from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import desc, func
from sqlalchemy.orm import Session, joinedload

from app.db.database import get_db
from app.models.models import Bookmark, Follow, Like, Notification, Reply, Retweet, Tweet, User
from app.schemas.schemas import BookmarkCreate, FollowCreate, LikeCreate, ReplyCreate, RetweetCreate, TweetCreate, TweetResponse
from app.services.users_service import get_current_user

router = APIRouter()


@router.post("/like", status_code=status.HTTP_201_CREATED)
def like_tweet(
    like_data: LikeCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Liker un tweet"""
    # Vérifier si le tweet existe
    tweet = db.query(Tweet).filter(Tweet.id == like_data.tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    # Vérifier si déjà liké
    existing_like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.tweet_id == like_data.tweet_id
    ).first()
    
    if existing_like:
        raise HTTPException(status_code=400, detail="Already liked")
    
    # Créer le like
    like = Like(user_id=current_user.id, tweet_id=like_data.tweet_id)
    db.add(like)
    
    # Incrémenter le compteur
    tweet.likes_count += 1
    
    # Créer une notification
    if tweet.user_id != current_user.id:
        notification = Notification(
            user_id=tweet.user_id,
            type="like",
            sender_id=current_user.id,
            tweet_id=tweet.id,
            content=f"{current_user.firstname} a aimé votre tweet"
        )
        db.add(notification)
    
    db.commit()
    db.refresh(like)
    
    return like


@router.delete("/like/{tweet_id}")
def unlike_tweet(
    tweet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retirer un like"""
    like = db.query(Like).filter(
        Like.user_id == current_user.id,
        Like.tweet_id == tweet_id
    ).first()
    
    if not like:
        raise HTTPException(status_code=404, detail="Like not found")
    
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if tweet:
        tweet.likes_count = max(0, tweet.likes_count - 1)
    
    db.delete(like)
    db.commit()
    
    return {"message": "Like removed successfully"}


@router.post("/retweet", status_code=status.HTTP_201_CREATED)
def retweet(
    retweet_data: RetweetCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retweeter un tweet"""
    tweet = db.query(Tweet).filter(Tweet.id == retweet_data.original_tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    existing_retweet = db.query(Retweet).filter(
        Retweet.user_id == current_user.id,
        Retweet.original_tweet_id == retweet_data.original_tweet_id
    ).first()
    
    if existing_retweet:
        raise HTTPException(status_code=400, detail="Already retweeted")
    
    retweet = Retweet(
        user_id=current_user.id,
        original_tweet_id=retweet_data.original_tweet_id,
        comment=retweet_data.comment
    )
    db.add(retweet)
    
    tweet.retweets_count += 1
    
    if tweet.user_id != current_user.id:
        notification = Notification(
            user_id=tweet.user_id,
            type="retweet",
            sender_id=current_user.id,
            tweet_id=tweet.id,
            content=f"{current_user.firstname} a retweeté votre tweet"
        )
        db.add(notification)
    
    db.commit()
    db.refresh(retweet)
    
    return retweet


@router.delete("/retweet/{tweet_id}")
def delete_retweet(
    tweet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Supprimer un retweet"""
    retweet = db.query(Retweet).filter(
        Retweet.user_id == current_user.id,
        Retweet.original_tweet_id == tweet_id
    ).first()
    
    if not retweet:
        raise HTTPException(status_code=404, detail="Retweet not found")
    
    tweet = db.query(Tweet).filter(Tweet.id == tweet_id).first()
    if tweet:
        tweet.retweets_count = max(0, tweet.retweets_count - 1)
    
    db.delete(retweet)
    db.commit()
    
    return {"message": "Retweet removed successfully"}


@router.post("/reply", status_code=status.HTTP_201_CREATED)
def reply_to_tweet(
    reply_data: ReplyCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Répondre à un tweet"""
    parent_tweet = db.query(Tweet).filter(Tweet.id == reply_data.parent_tweet_id).first()
    if not parent_tweet:
        raise HTTPException(status_code=404, detail="Parent tweet not found")
    
    # Créer le tweet de réponse
    reply_tweet = Tweet(
        user_id=current_user.id,
        content=reply_data.content
    )
    db.add(reply_tweet)
    db.flush()
    
    # Créer la relation de réponse
    reply = Reply(
        tweet_id=reply_tweet.id,
        parent_tweet_id=reply_data.parent_tweet_id
    )
    db.add(reply)
    
    # Incrémenter le compteur
    parent_tweet.replies_count += 1
    
    # Créer une notification
    if parent_tweet.user_id != current_user.id:
        notification = Notification(
            user_id=parent_tweet.user_id,
            type="reply",
            sender_id=current_user.id,
            tweet_id=parent_tweet.id,
            content=f"{current_user.firstname} a répondu à votre tweet"
        )
        db.add(notification)
    
    db.commit()
    db.refresh(reply_tweet)
    
    return {
        **reply_tweet.__dict__,
        "author": current_user,
        "parent_tweet_id": reply_data.parent_tweet_id
    }


@router.get("/{tweet_id}/replies")
def get_tweet_replies(
    tweet_id: int,
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user),
):
    replies = (
        db.query(Tweet)
        .join(Reply, Reply.tweet_id == Tweet.id)
        .options(joinedload(Tweet.user))
        .filter(Reply.parent_tweet_id == tweet_id)
        .order_by(desc(Tweet.created_at))
        .offset(offset)
        .limit(limit)
        .all()
    )

    total_count = (
        db.query(func.count(Reply.id))
        .filter(Reply.parent_tweet_id == tweet_id)
        .scalar()
    )

    out = []
    for tw in replies:
        is_liked = False
        is_retweeted = False
        is_bookmarked = False

        if current_user:
            is_liked = db.query(Like).filter_by(user_id=current_user.id, tweet_id=tw.id).first() is not None
            is_retweeted = db.query(Retweet).filter_by(user_id=current_user.id, original_tweet_id=tw.id).first() is not None
            is_bookmarked = db.query(Bookmark).filter_by(user_id=current_user.id, tweet_id=tw.id).first() is not None

        out.append(
            TweetResponse(
                id=tw.id,
                user_id=tw.user_id,
                content=tw.content,
                image_url=tw.image_url,
                video_url=tw.video_url,
                created_at=tw.created_at,
                updated_at=tw.updated_at,
                likes_count=tw.likes_count,
                retweets_count=tw.retweets_count,
                replies_count=tw.replies_count,
                author=tw.user,
                hashtags=[],
                is_liked=is_liked,
                is_retweeted=is_retweeted,
                is_bookmarked=is_bookmarked,
            )
        )

    return {"replies": out, "total_count": total_count}

@router.post("/bookmark", status_code=status.HTTP_201_CREATED)
def bookmark_tweet(
    bookmark_data: BookmarkCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Sauvegarder un tweet"""
    tweet = db.query(Tweet).filter(Tweet.id == bookmark_data.tweet_id).first()
    if not tweet:
        raise HTTPException(status_code=404, detail="Tweet not found")
    
    existing_bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.tweet_id == bookmark_data.tweet_id
    ).first()
    
    if existing_bookmark:
        raise HTTPException(status_code=400, detail="Already bookmarked")
    
    bookmark = Bookmark(user_id=current_user.id, tweet_id=bookmark_data.tweet_id)
    db.add(bookmark)
    db.commit()
    db.refresh(bookmark)
    
    return bookmark


@router.delete("/bookmark/{tweet_id}")
def delete_bookmark(
    tweet_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Retirer un bookmark"""
    bookmark = db.query(Bookmark).filter(
        Bookmark.user_id == current_user.id,
        Bookmark.tweet_id == tweet_id
    ).first()
    
    if not bookmark:
        raise HTTPException(status_code=404, detail="Bookmark not found")
    
    db.delete(bookmark)
    db.commit()
    
    return {"message": "Bookmark removed successfully"}

@router.get("/bookmarks")
def get_bookmarks(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Obtenir ses bookmarks"""
    bookmarks = db.query(Bookmark).filter(Bookmark.user_id == current_user.id).order_by(desc(Bookmark.created_at)).offset(offset).limit(limit).all()
    
    bookmark_responses = []
    for bookmark in bookmarks:
        tweet = bookmark.tweet
        is_liked = db.query(Like).filter(Like.user_id == current_user.id, Like.tweet_id == tweet.id).first() is not None
        
        bookmark_responses.append({
            "id": bookmark.id,
            "created_at": bookmark.created_at,
            "tweet": {
                **tweet.__dict__,
                "author": tweet.user,
                "is_liked": is_liked
            }
        })
    
    total_count = db.query(func.count(Bookmark.id)).filter(Bookmark.user_id == current_user.id).scalar()
    
    return {
        "bookmarks": bookmark_responses,
        "total_count": total_count
    }


@router.post("/follow", status_code=status.HTTP_201_CREATED)
def follow_user(
    follow_data: FollowCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Suivre un utilisateur"""
    # Vérifier si l'utilisateur existe
    user_to_follow = db.query(User).filter(User.id == follow_data.following_id).first()
    if not user_to_follow:
        raise HTTPException(status_code=404, detail="User not found")

    # Empêcher de se suivre soi-même
    if follow_data.following_id == current_user.id:
        raise HTTPException(status_code=400, detail="Cannot follow yourself")

    # Vérifier si déjà suivi
    existing_follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == follow_data.following_id
    ).first()

    if existing_follow:
        raise HTTPException(status_code=400, detail="Already following this user")

    # Créer le follow
    follow = Follow(follower_id=current_user.id, following_id=follow_data.following_id)
    db.add(follow)

    # Créer une notification
    notification = Notification(
        user_id=follow_data.following_id,
        type="follow",
        sender_id=current_user.id,
        content=f"{current_user.firstname} {current_user.lastname} a commencé à vous suivre"
    )
    db.add(notification)

    db.commit()
    db.refresh(follow)

    return follow


@router.delete("/follow/{user_id}")
def unfollow_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Ne plus suivre un utilisateur"""
    follow = db.query(Follow).filter(
        Follow.follower_id == current_user.id,
        Follow.following_id == user_id
    ).first()

    if not follow:
        raise HTTPException(status_code=404, detail="Not following this user")

    db.delete(follow)
    db.commit()

    return {"message": "Unfollowed successfully"}