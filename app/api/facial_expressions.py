from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.db.database import get_db
from app.models.models import FacialExpression, User
from app.schemas.schemas import (
    FacialExpressionCreate,
    FacialExpressionResponse,
    EmotionAnalysisResponse
)
from app.services.users_service import get_current_user
from app.services.facial_recognition_service import analyze_facial_expression, get_dominant_emotion

router = APIRouter()


@router.post("/analyze", response_model=EmotionAnalysisResponse)
async def analyze_emotion(
    data: FacialExpressionCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    save: bool = True
):
    """
    Analyze facial expression from webcam image
    
    - Analyzes emotion from base64 image
    - Optionally saves to database
    - Returns all emotions with confidence scores
    """
    try:
        # Analyze the image
        emotions = analyze_facial_expression(data.image_data)
        if emotions is None:
            raise ValueError("Failed to analyze facial expression")
        dominant_emotion, confidence = get_dominant_emotion(emotions)
        
        expression_id = None
        
        # Save to database if requested
        if save:
            facial_expression = FacialExpression(
                user_id=current_user.id,
                tweet_id=data.tweet_id,
                emotion=dominant_emotion,
                confidence=confidence
            )
            db.add(facial_expression)
            db.commit()
            db.refresh(facial_expression)
            expression_id = facial_expression.id
        
        return EmotionAnalysisResponse(
            emotions=emotions,
            dominant_emotion=dominant_emotion,
            confidence=confidence,
            saved=save,
            expression_id=expression_id
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error analyzing facial expression: {str(e)}"
        )


@router.get("/history", response_model=List[FacialExpressionResponse])
def get_expression_history(
    limit: int = 20,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's facial expression history"""
    expressions = (
        db.query(FacialExpression)
        .filter(FacialExpression.user_id == current_user.id)
        .order_by(FacialExpression.created_at.desc())
        .limit(limit)
        .all()
    )
    
    return expressions


@router.get("/current-mood")
def get_current_mood(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's most recent emotion"""
    latest_expression = (
        db.query(FacialExpression)
        .filter(FacialExpression.user_id == current_user.id)
        .order_by(FacialExpression.created_at.desc())
        .first()
    )
    
    if not latest_expression:
        return {"mood": "neutral", "confidence": 0.0}
    
    return {
        "mood": latest_expression.emotion,
        "confidence": latest_expression.confidence,
        "analyzed_at": latest_expression.created_at
    }