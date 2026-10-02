from dotenv import load_dotenv
load_dotenv()

from app.router import (
    auth_route, 
    user_route, 
    channel_route, 
    video_route, 
    history_route, 
    comment_route
)

from sqlmodel import SQLModel
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


from app.configs import cloudinary
from app.middlewares.auth_middleware import AuthMiddleware


from app.models import *
from app.configs.db import engine
from app.configs.rediss import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    yield
    await redis_client.aclose()


app = FastAPI(lifespan = lifespan)

# Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(AuthMiddleware)


# Routes
app.include_router(auth_route.router)
app.include_router(user_route.router)
app.include_router(channel_route.router)
app.include_router(video_route.router)
app.include_router(history_route.router)
app.include_router(comment_route.router)