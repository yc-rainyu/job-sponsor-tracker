from typing import Literal

from pydantic import BaseModel


class Health(BaseModel):
    status: Literal['ok']
    db: Literal['ok']
    version: str
