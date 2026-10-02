from sqlalchemy import LargeBinary
from sqlmodel import SQLModel, Field, Relationship, Column


from typing import Optional
from datetime import date


class User(SQLModel, table = True):
    __tablename__ = "users"

    id: str = Field(
        primary_key = True
    )

    email: str = Field(
        unique = True
    )

    password: Optional[str] = None

    is_streamer: bool = Field(
        default = False
    )

    display_picture: Optional[bytes] = Field(
        default = None, 
        sa_column = Column(LargeBinary)
    )

    joined_on: date = Field(
        default_factory = date.today
    )

    channel: Optional["Channel"] = Relationship(back_populates = "user", sa_relationship_kwargs={"passive_deletes": True}) # type: ignore
    comments: list["Comment"] = Relationship(back_populates = "sender", sa_relationship_kwargs={"passive_deletes": True}) # type: ignore
    history: list["History"] = Relationship(back_populates = "user", sa_relationship_kwargs={"passive_deletes": True}) # type: ignore
    following: list["Follower"] = Relationship(back_populates="follower", sa_relationship_kwargs={"passive_deletes": True})   # type: ignore
    likes: list["Like"] = Relationship(back_populates="user", sa_relationship_kwargs={"passive_deletes": True})   # type: ignore
