from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import DateTime, String, Text, Integer, Float, Boolean, ForeignKey, Table, Column, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..db.database import Base

# N-to-N relation
TweetHashtag = Table(
    "tweet_hashtags",
    Base.metadata,
    Column("tweet_id", Integer, ForeignKey("tweets.id", ondelete="CASCADE"), primary_key=True),
    Column("hashtag_id", Integer, ForeignKey("hashtags.id", ondelete="CASCADE"), primary_key=True)
)


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    lastname: Mapped[str] = mapped_column(String(255))
    firstname: Mapped[str] = mapped_column(String(255))
    username: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    
    # Optional profile fields
    bio: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    profile_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    banner_image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, server_default="true")

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now()
    )

    # Relationships
    tweets: Mapped[List["Tweet"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    likes: Mapped[List["Like"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    retweets: Mapped[List["Retweet"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    bookmarks: Mapped[List["Bookmark"]] = relationship(back_populates="user", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship(
        foreign_keys="[Notification.user_id]",
        back_populates="user",
        cascade="all, delete-orphan"
    )
    facial_expressions: Mapped[List["FacialExpression"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan"
    )
    
    # Following relationships
    followers: Mapped[List["Follow"]] = relationship(
        foreign_keys="[Follow.following_id]",
        back_populates="following",
        cascade="all, delete-orphan"
    )
    following: Mapped[List["Follow"]] = relationship(
        foreign_keys="[Follow.follower_id]",
        back_populates="follower",
        cascade="all, delete-orphan"
    )


class Tweet(Base):
    __tablename__ = "tweets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    
    # Media
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    video_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    likes_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    retweets_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    replies_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    
    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        onupdate=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="tweets")
    likes: Mapped[List["Like"]] = relationship(back_populates="tweet", cascade="all, delete-orphan")
    retweets: Mapped[List["Retweet"]] = relationship(back_populates="original_tweet", cascade="all, delete-orphan")
    bookmarks: Mapped[List["Bookmark"]] = relationship(back_populates="tweet", cascade="all, delete-orphan")
    hashtags: Mapped[List["Hashtag"]] = relationship(secondary=TweetHashtag, back_populates="tweets")
    mentions: Mapped[List["Mention"]] = relationship(back_populates="tweet", cascade="all, delete-orphan")
    notifications: Mapped[List["Notification"]] = relationship(back_populates="tweet", cascade="all, delete-orphan")
    facial_expressions: Mapped[List["FacialExpression"]] = relationship(back_populates="tweet")
    
    # Reply relationships
    reply: Mapped[Optional["Reply"]] = relationship(
        foreign_keys="[Reply.tweet_id]",
        back_populates="tweet",
        uselist=False,
        cascade="all, delete-orphan"
    )
    replies: Mapped[List["Reply"]] = relationship(
        foreign_keys="[Reply.parent_tweet_id]",
        back_populates="parent_tweet",
        cascade="all, delete-orphan"
    )


class Like(Base):
    __tablename__ = "likes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False, index=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="likes")
    tweet: Mapped["Tweet"] = relationship(back_populates="likes")


class Retweet(Base):
    __tablename__ = "retweets"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    original_tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    comment: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="retweets")
    original_tweet: Mapped["Tweet"] = relationship(back_populates="retweets")


class Reply(Base):
    __tablename__ = "replies"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id", ondelete="CASCADE"),
        nullable=False,
        unique=True
    )
    parent_tweet_id: Mapped[int] = mapped_column(
        ForeignKey("tweets.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    tweet: Mapped["Tweet"] = relationship(foreign_keys=[tweet_id], back_populates="reply")
    parent_tweet: Mapped["Tweet"] = relationship(foreign_keys=[parent_tweet_id], back_populates="replies")


class Follow(Base):
    __tablename__ = "follows"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    follower_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    following_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    follower: Mapped["User"] = relationship(foreign_keys=[follower_id], back_populates="following")
    following: Mapped["User"] = relationship(foreign_keys=[following_id], back_populates="followers")


class Hashtag(Base):
    __tablename__ = "hashtags"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    usage_count: Mapped[int] = mapped_column(Integer, default=0, server_default="0")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    tweets: Mapped[List["Tweet"]] = relationship(secondary=TweetHashtag, back_populates="hashtags")


class Mention(Base):
    __tablename__ = "mentions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
    mentioned_user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    tweet: Mapped["Tweet"] = relationship(back_populates="mentions")
    mentioned_user: Mapped["User"] = relationship()


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    type: Mapped[str] = mapped_column(String(50), nullable=False)  # 'like', 'retweet', 'reply', 'follow', 'mention'
    sender_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True)
    tweet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"), nullable=True)
    content: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, server_default="false")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True
    )
    
    # Relationships
    user: Mapped["User"] = relationship(foreign_keys=[user_id], back_populates="notifications")
    sender: Mapped[Optional["User"]] = relationship(foreign_keys=[sender_id])
    tweet: Mapped[Optional["Tweet"]] = relationship(back_populates="notifications")


class Bookmark(Base):
    __tablename__ = "bookmarks"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tweet_id: Mapped[int] = mapped_column(ForeignKey("tweets.id", ondelete="CASCADE"), nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="bookmarks")
    tweet: Mapped["Tweet"] = relationship(back_populates="bookmarks")


class FacialExpression(Base):
    __tablename__ = "facial_expressions"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    tweet_id: Mapped[Optional[int]] = mapped_column(ForeignKey("tweets.id", ondelete="SET NULL"), nullable=True)
    emotion: Mapped[str] = mapped_column(
        String(20),
        nullable=False
    )  # 'joy', 'sadness', 'anger', 'surprise', 'disgust', 'fear', 'neutral'
    confidence: Mapped[float] = mapped_column(Float, nullable=False)
    image_url: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # Relationships
    user: Mapped["User"] = relationship(back_populates="facial_expressions")
    tweet: Mapped[Optional["Tweet"]] = relationship(back_populates="facial_expressions")