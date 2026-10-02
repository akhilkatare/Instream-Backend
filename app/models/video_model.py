from sqlmodel import SQLModel, Field, Relationship

from typing import Optional
from datetime import datetime


class Video(SQLModel, table = True):
    __tablename__ = "videos"

    id: str = Field(
        primary_key = True
    )

    channel_id: str = Field(
        foreign_key = "channels.id", 
        ondelete = "CASCADE", 
        index = True
    )

    title: str

    description: str

    duration: int

    video_url: str = Field(
        unique = True
    )

    video_public_id: str = Field(
        unique = True
    )

    thumbnail_url: str = Field(
        unique = True
    )

    thumbnail_public_id: str = Field(
        unique = True
    )

    views: int = Field(
        default = 0
    )

    uploaded_at: datetime = Field(
        default_factory = datetime.now
    )


    channel: Optional["Channel"] = Relationship(back_populates = "videos") # type: ignore
    comments: list["Comment"] = Relationship(back_populates = "video", sa_relationship_kwargs={"passive_deletes": True}) # type: ignore
    histories: list["History"] = Relationship(back_populates = "video", sa_relationship_kwargs={"passive_deletes": True}) # type: ignore
    likes: list["Like"] = Relationship(back_populates="video", sa_relationship_kwargs={"passive_deletes": True})  # type: ignore
    