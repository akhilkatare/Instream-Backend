from datetime import date
from typing import Optional, TYPE_CHECKING

from sqlmodel import SQLModel, Field, Relationship, UniqueConstraint

if TYPE_CHECKING:
    from app.models.user_model import User
    from app.models.channel_model import Channel


class Follower(SQLModel, table=True):
    __tablename__ = "followers"

    # A user can follow a channel only once.
    __table_args__ = (
        UniqueConstraint("follower_id", "channel_id", name="uq_follower_channel"),
    )

    id: str = Field(
        primary_key = True
    )

    follower_id: str = Field(
        foreign_key = "users.id", 
        index=True, 
        ondelete = "CASCADE"
    )

    channel_id: str = Field(
        foreign_key = "channels.id", 
        index=True, 
        ondelete = "CASCADE"
    )

    followed_on: date = Field(
        default_factory = date.today
    )


    follower: Optional["User"] = Relationship(back_populates="following")     # type: ignore
    channel: Optional["Channel"] = Relationship(back_populates="followers")   # type: ignore
