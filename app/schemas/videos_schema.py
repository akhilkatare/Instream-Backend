from pydantic import BaseModel


class CreateVideoSchema(BaseModel):
    title: str
    description: str
    duration: int
    video_url: str
    video_public_id: str
    thumbnail_url: str
    thumbnail_public_id: str
