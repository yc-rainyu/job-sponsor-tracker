from fastapi import FastAPI

from app.routers import health

app = FastAPI(title='Job Sponsor Tracker API')
app.include_router(health.router)
