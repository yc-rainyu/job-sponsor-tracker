import datetime
import uuid

from pydantic import BaseModel, ConfigDict


class GoogleSignInBody(BaseModel):
    credential: str


class DemoBody(BaseModel):
    # the browser's local date, so the demo's newest application is the user's today
    today: datetime.date | None = None


class Me(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None
    display_name: str | None
    avatar_url: str | None
    is_demo: bool
