from fastapi import FastAPI

from app.routers import health, sponsors

app = FastAPI(title='Job Sponsor Tracker API')
app.include_router(health.router)
app.include_router(sponsors.router)
