from sqlmodel import SQLModel, Field, Relationship

from typing import Optional
from datetime import date


class Channel(SQLModel, table = True):
    __tablename__ = "channels"

    id: str = Field(
        primary_key = True,
    )

    user_id: str = Field (
        foreign_key = "users.id", 
        ondelete = "CASCADE", 
        unique = True
    )

    name: str = Field(
        unique = True, 
        index = True
    )

    description: str

    created_on: date = Field(
        default_factory = date.today
    )


    user: Optional["User"] = Relationship(back_populates = "channel") # type: ignore
    videos: list["Video"] = Relationship(back_populates = "channel", sa_relationship_kwargs={"passive_deletes": True}) # type: ignore
    followers: list["Follower"] = Relationship(back_populates="channel", sa_relationship_kwargs={"passive_deletes": True})   # type: ignore