from sqlmodel import SQLModel, Field, Relationship

from typing import Optional
from datetime import date


class History(SQLModel, table = True):
    __tablename__ = "histories"

    id: str = Field(
        primary_key = True
    )

    user_id: str = Field(
        foreign_key = "users.id", 
        index = True, 
        ondelete = "CASCADE"
    )

    video_id: str = Field(
        foreign_key = "videos.id", 
        ondelete = "CASCADE"
    )

    watched_on: date = Field(
        default_factory = date.today
    )


    user: Optional["User"] = Relationship(back_populates = "history") # type: ignore
    video: Optional["Video"] = Relationship(back_populates = "histories") # type: ignore