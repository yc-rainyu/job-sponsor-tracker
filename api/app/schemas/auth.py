import uuid

from pydantic import BaseModel, ConfigDict


class GoogleSignInBody(BaseModel):
    credential: str


class Me(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: str | None
    display_name: str | None
    avatar_url: str | None
    is_demo: bool
