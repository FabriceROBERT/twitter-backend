from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.db.database import engine, Base
from app.core.config import settings
from app.api import auth ,interactions, users, tweets, facial_expressions

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

# Include routers
app.include_router(auth.router, prefix="/api/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/api/users", tags=["Users"])
app.include_router(tweets.router, prefix="/api/tweets", tags=["Tweets"])
app.include_router(interactions.router, prefix="/api/interactions", tags=["Interactions"])
app.include_router(facial_expressions.router, prefix="/api/facial-expressions", tags=["facial-expressions"]) 


@app.get("/")
def root():
    return {"message": "Twitter Clone API", "status": "running"}
