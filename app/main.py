from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import (
    health,
    auth,
    profiles,
    activities,
    community,
    progress,
    recommendations,
    challenges,
    strava,
    events,
    catalogue,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    from seed_tyres import seed
    await seed()
    yield


app = FastAPI(title="Michelin Riding API", version="1.0.0", lifespan=lifespan)

origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:8081",
    "http://127.0.0.1:8081",
    "http://localhost:19006",
    "http://127.0.0.1:19006",
    "https://cycling-web-production.up.railway.app",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(activities.router)
app.include_router(community.router)
app.include_router(progress.router)
app.include_router(recommendations.router)
app.include_router(challenges.router)
app.include_router(strava.router)
app.include_router(events.router)
app.include_router(catalogue.router)


@app.get("/")
async def root():
    return {"message": "Michelin Riding API"}