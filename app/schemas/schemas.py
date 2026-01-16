from pydantic import BaseModel, EmailStr, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from enum import Enum
import re


class UserRegister(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=8)
    firstname: str = Field(..., min_length=1, max_length=255)
    lastname: str = Field(..., min_length=1, max_length=255)
    
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """Validate username format"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must contain only letters, numbers, and underscores')
        return v.lower()
    
    @field_validator('password')
    @classmethod
    def validate_password(cls, v: str) -> str:
        """Validate password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v
    
    @field_validator('firstname', 'lastname')
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate name fields"""
        v = v.strip()
        if not v:
            raise ValueError('Name cannot be empty')
        return v.title()  # Capitalize first letter


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    firstname: str
    lastname: str
    bio: Optional[str] = None
    profile_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None
    is_active: bool
    
    model_config = {"from_attributes": True}


class UserUpdate(BaseModel):
    firstname: Optional[str] = Field(None, min_length=1, max_length=255)
    lastname: Optional[str] = Field(None, min_length=1, max_length=255)
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = Field(None, max_length=500)
    profile_image_url: Optional[str] = None
    banner_image_url: Optional[str] = None


class ChangePasswordRequest(BaseModel):
    current_password: str
    new_password: str = Field(..., min_length=8)
    
    @field_validator('new_password')
    @classmethod
    def validate_new_password(cls, v: str) -> str:
        """Validate new password strength"""
        if len(v) < 8:
            raise ValueError('Password must be at least 8 characters')
        if not any(char.isdigit() for char in v):
            raise ValueError('Password must contain at least one digit')
        if not any(char.islower() for char in v):
            raise ValueError('Password must contain at least one lowercase letter')
        if not any(char.isupper() for char in v):
            raise ValueError('Password must contain at least one uppercase letter')
        return v


# Enums
class NotificationType(str, Enum):
    LIKE = "like"
    RETWEET = "retweet"
    REPLY = "reply"
    FOLLOW = "follow"
    MENTION = "mention"


class EmotionType(str, Enum):
    JOY = "joy"
    SADNESS = "sadness"
    ANGER = "anger"
    SURPRISE = "surprise"
    DISGUST = "disgust"
    FEAR = "fear"
    NEUTRAL = "neutral"


#  User Schemas 

class UserBase(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    email: EmailStr
    display_name: Optional[str] = Field(None, max_length=100)
    bio: Optional[str] = None


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)



class UserProfile(UserResponse):
    followers_count: int = 0
    following_count: int = 0
    tweets_count: int = 0


#  Tweet Schemas 

class TweetBase(BaseModel):
    content: str = Field(..., min_length=1, max_length=280)
    image_url: Optional[str] = None
    video_url: Optional[str] = None


class TweetCreate(TweetBase):
    parent_tweet_id: Optional[int] = None  # For replies


class TweetUpdate(BaseModel):
    content: Optional[str] = Field(None, min_length=1, max_length=280)


class TweetResponse(TweetBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime
    likes_count: int
    retweets_count: int
    replies_count: int
    
    # Relations
    author: UserResponse
    hashtags: List[str] = []
    is_liked: bool = False
    is_retweeted: bool = False
    is_bookmarked: bool = False
    
    model_config = ConfigDict(from_attributes=True)


class TweetWithReplies(TweetResponse):
    parent_tweet: Optional[TweetResponse] = None
    replies: List[TweetResponse] = []


#  Like Schemas 

class LikeCreate(BaseModel):
    tweet_id: int


class LikeResponse(BaseModel):
    id: int
    user_id: int
    tweet_id: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


#  Retweet Schemas 

class RetweetCreate(BaseModel):
    original_tweet_id: int
    comment: Optional[str] = Field(None, max_length=280)


class RetweetResponse(BaseModel):
    id: int
    user_id: int
    original_tweet_id: int
    comment: Optional[str]
    created_at: datetime
    user: UserResponse
    original_tweet: TweetResponse
    
    model_config = ConfigDict(from_attributes=True)

#  Reply Schemas 


class ReplyCreate(BaseModel):
    parent_tweet_id: int
    content: str = Field(..., min_length=1, max_length=280)


#  Follow Schemas 

class FollowCreate(BaseModel):
    following_id: int


class FollowResponse(BaseModel):
    id: int
    follower_id: int
    following_id: int
    created_at: datetime
    follower: UserResponse
    following: UserResponse
    
    model_config = ConfigDict(from_attributes=True)


#  Hashtag Schemas 

class HashtagResponse(BaseModel):
    id: int
    name: str
    usage_count: int
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class HashtagTrending(BaseModel):
    name: str
    usage_count: int
    tweets_count: int


#  Notification Schemas 

class NotificationResponse(BaseModel):
    id: int
    user_id: int
    type: NotificationType
    sender_id: Optional[int]
    tweet_id: Optional[int]
    content: str
    is_read: bool
    created_at: datetime
    sender: Optional[UserResponse] = None
    
    model_config = ConfigDict(from_attributes=True)


class NotificationUpdate(BaseModel):
    is_read: bool


#  Bookmark Schemas 

class BookmarkCreate(BaseModel):
    tweet_id: int


class BookmarkResponse(BaseModel):
    id: int
    user_id: int
    tweet_id: int
    created_at: datetime
    tweet: TweetResponse
    
    model_config = ConfigDict(from_attributes=True)


# Facial Expression Schemas 

class FacialExpressionCreate(BaseModel):
    image_data: str = Field(..., description="Base64 encoded image")
    tweet_id: Optional[int] = None

class FacialExpressionResponse(BaseModel):
    id: int
    user_id: int
    tweet_id: Optional[int]
    emotion: str
    confidence: float
    created_at: datetime
    
    class Config:
        from_attributes = True

class EmotionAnalysisResponse(BaseModel):
    emotions: dict[str, float]
    dominant_emotion: str
    confidence: float
    saved: bool = False
    expression_id: Optional[int] = None


# Search Schemas

class SearchQuery(BaseModel):
    query: str = Field(..., min_length=1)
    type: Optional[str] = Field("all", pattern="^(all|tweets|users|hashtags)$")
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class SearchResponse(BaseModel):
    tweets: List[TweetResponse] = []
    users: List[UserResponse] = []
    hashtags: List[HashtagResponse] = []
    total_count: int


#  Feed Schemas 

class FeedQuery(BaseModel):
    limit: int = Field(20, ge=1, le=100)
    offset: int = Field(0, ge=0)


class FeedResponse(BaseModel):
    tweets: List[TweetResponse]
    has_more: bool
    total_count: int


#  Authentication Schemas 

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class TokenData(BaseModel):
    user_id: Optional[UUID] = None