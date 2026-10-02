from typing import Optional
from sqlalchemy import UniqueConstraint
from sqlmodel import SQLModel, Field, Relationship


class Like(SQLModel, table=True):
    __tablename__ = "likes"

    __table_args__ = (
        UniqueConstraint("user_id", "video_id", name="uq_like_user_video"),
    )

    id: str = Field(
        primary_key = True
    )

    user_id: str = Field(
        foreign_key = "users.id", 
        ondelete = "CASCADE", 
        index = True
    )

    video_id: str = Field(
        foreign_key = "videos.id", 
        ondelete = "CASCADE", 
        index = True
    )


    user: Optional["User"] = Relationship(back_populates="likes")      # type: ignore
    video: Optional["Video"] = Relationship(back_populates="likes")    # type: ignore
