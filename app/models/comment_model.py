from sqlmodel import SQLModel, Field, Relationship

from typing import Optional
from datetime import datetime


class Comment(SQLModel, table = True):
    __tablename__ = "comments"

    id: str = Field(
        primary_key = True
    )

    video_id: str = Field(
        foreign_key = "videos.id", 
        ondelete = "CASCADE"
    )

    sender_id: str = Field(
        foreign_key = "users.id", 
        ondelete = "CASCADE"
    )

    comment: str

    commented_at: datetime = Field(
        default_factory = datetime.now
    )


    video: Optional["Video"] = Relationship(back_populates = "comments") # type: ignore
    sender: Optional["User"] = Relationship(back_populates = "comments") # type: ignore