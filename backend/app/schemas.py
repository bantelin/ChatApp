from datetime import datetime

from pydantic import BaseModel


class MessageOut(BaseModel):
    id: int
    username: str
    trip: str | None
    content: str
    created_at: datetime
    avatar_url: str | None = None

    class Config:
        from_attributes = True


class AvatarOut(BaseModel):
    trip: str
    avatar_url: str | None
