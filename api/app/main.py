from fastapi import FastAPI

from app.routers import auth, health, jd, sponsors

app = FastAPI(title='Job Sponsor Tracker API')
app.include_router(health.router)
app.include_router(sponsors.router)
app.include_router(jd.router)
app.include_router(auth.router)
