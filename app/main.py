from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from sqlalchemy.orm import Session
from app.db.database import engine, Base, get_db
from app.core.config import settings

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Twitter Clone API",
    description="Social media platform API",
)

origins = [settings.front_url]

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"message": "Twitter Clone API", "status": "running"}

@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    """Check API and database health"""
    try:
        # Test database connection
        db.execute(text("SELECT 1"))
        return {
            "status": "healthy",
            "database": "connected",
            "api": "running"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503, 
            detail=f"Database connection failed: {str(e)}"
        )

@app.get("/health/db")
def database_health(db: Session = Depends(get_db)):
    """Detailed database health check"""
    try:
        # Test connection
        result = db.execute(text("SELECT version()")).scalar()
        
        # Count tables
        tables_query = text("""
            SELECT COUNT(*) 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
        """)
        table_count = db.execute(tables_query).scalar()
        
        return {
            "status": "connected",
            "postgres_version": result,
            "tables_count": table_count,
            "database_url": settings.database_url.split("@")[1] if "@" in settings.database_url else "hidden"
        }
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail=f"Database error: {str(e)}"
        )