import datetime
import uuid
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field


class GoogleSignInBody(BaseModel):
    # well above any Google ID token, so it only stops oversized bodies
    credential: Annotated[str, Field(max_length=4096)]


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
