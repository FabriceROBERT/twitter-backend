from transformers import pipeline
from PIL import Image
import io
import base64
from typing import Dict, Optional
import logging

logger = logging.getLogger(__name__)

# Initialize the emotion classification pipeline
try:
    emotion_classifier = pipeline("image-classification", model="hilmansw/emotion_classification")
except Exception as e:
    logger.error(f"Failed to load emotion classification model: {e}")
    emotion_classifier = None


def analyze_facial_expression(image_data: str) -> Optional[Dict[str, float]]:
    if not emotion_classifier:
        raise RuntimeError("Emotion classifier not initialized")
    
    try:
        # Remove base64 prefix if present
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        # Decode base64 to image
        image_bytes = base64.b64decode(image_data)
        image = Image.open(io.BytesIO(image_bytes))
        
        results = emotion_classifier(image)
        
        # Convert to dict
        emotions = {result['label'].lower(): result['score'] for result in results}
        
        return emotions
    
    except Exception as e:
        logger.error(f"Error analyzing facial expression: {e}")
        raise


def get_dominant_emotion(emotions: Dict[str, float]) -> tuple[str, float]:
    """Get the emotion with highest confidence"""
    return max(emotions.items(), key=lambda x: x[1])