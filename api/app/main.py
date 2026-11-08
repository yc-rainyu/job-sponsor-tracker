from fastapi import FastAPI

from app.core.settings import settings
from app.routers import applications, auth, health, jd, sponsors


def docs_urls(app_env: str) -> dict[str, None]:
    if app_env == 'prod':
        return {'docs_url': None, 'redoc_url': None, 'openapi_url': None}
    return {}


app = FastAPI(title='Job Sponsor Tracker API', **docs_urls(settings.app_env))
app.include_router(health.router)
app.include_router(sponsors.router)
app.include_router(jd.router)
app.include_router(auth.router)
app.include_router(applications.router)
