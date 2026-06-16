from fastapi import FastAPI
from app.routers import health, auth, profiles, activities, community, progress, recommendations, challenges

app = FastAPI(title="Michelin Riding API", version="1.0.0")

app.include_router(health.router)
app.include_router(auth.router)
app.include_router(profiles.router)
app.include_router(activities.router)
app.include_router(community.router)
app.include_router(progress.router)
app.include_router(recommendations.router)
app.include_router(challenges.router)


@app.get("/")
async def root():
    return {"message": "Michelin Riding API"}
