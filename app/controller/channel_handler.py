import uuid

from fastapi import (
    status,
    Depends, 
    Request, 
    HTTPException, 
)

from app.schemas import (
    ApiResponse, 
    CreateChannelSchema, 
    UpdateChannelNameSchema, 
    UpdateDescriptionSchema,
)

from sqlite3 import IntegrityError
from sqlmodel import Session, func, select

from app.types import ResponseStatusType
from app.configs.db import get_db_session
from app.models import Channel, User, Follower


def _get_owned_channel(db_session: Session, user_id: str) -> Channel:
    """Fetch the caller's channel or 404. Used by all owner-only operations."""

    channel = db_session.exec(select(Channel).where(Channel.user_id == user_id)).first()

    if channel is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "You don't have a channel yet."
        )
    
    return channel


async def handle_create_channel(
    request: Request, 
    data: CreateChannelSchema, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    user_account = db_session.get(User, user_id)

    if not user_account:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "User not found."
        )

    if db_session.exec(select(Channel).where(Channel.user_id == user_id)).first():
        raise HTTPException(
            status.HTTP_409_CONFLICT, 
            "You already have a channel."
        )

    if db_session.exec(select(Channel).where(Channel.name == data.name)).first():
        raise HTTPException(
            status.HTTP_409_CONFLICT, 
            "Channel name is already taken."
        )

    channel = Channel(
        id = uuid.uuid4().hex,
        user_id = user_id,
        name = data.name,
        description = data.description
    )

    user_account.is_streamer = True
    db_session.add(channel)

    try:
        db_session.commit()

    except IntegrityError:
        db_session.rollback()

        raise HTTPException(
            status.HTTP_409_CONFLICT, 
            "Channel already exists."
        )

    db_session.refresh(channel)

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Channel created.",
        data = {
            "channel_id": channel.id, 
            "name": channel.name
        },
    )


async def handle_get_my_channel(
    request: Request, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    channel = db_session.exec(select(Channel).where(Channel.user_id == user_id)).first()
    
    if channel is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "You don't have a channel yet."
        )

    followers_count = db_session.exec(
        select(func.count(Follower.id)).where(Follower.channel_id == channel.id)
    ).one()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Channel fetched.",
        data = {
            "id": channel.id, 
            "name": channel.name, 
            "description": channel.description, 
            "followers": followers_count
        },
    )


async def handle_get_following(
    request: Request,
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id

    rows = db_session.exec(
        select(Channel, Follower.followed_on)
        .join(Follower, Follower.channel_id == Channel.id)
        .where(Follower.follower_id == user_id)
        .order_by(Follower.followed_on.desc())
    ).all()

    channels = [
        {
            "id": c.id,
            "name": c.name,
            "description": c.description,
            "followed_on": followed_on,
        }
        for c, followed_on in rows
    ]

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Following channels fetched.",
        data = {"channels": channels},
    )


async def handle_view_channel(
    request: Request, 
    channel_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    channel = db_session.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Channel not found."
        )

    followers = db_session.exec(
        select(func.count(Follower.id)).where(Follower.channel_id == channel_id)
    ).one()

    user_id = getattr(request.state, "user_id", None)
    is_following = False

    if user_id:
        is_following = db_session.exec(
            select(Follower.id).where(
                Follower.follower_id == user_id, Follower.channel_id == channel_id
            )
        ).first() is not None

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Channel fetched.",
        data = {
            "id": channel.id,
            "name": channel.name,
            "description": channel.description,
            "followers": followers,
            "is_following": is_following,
        },
    )


async def handle_update_channel_name(
        request: Request, 
        data: UpdateChannelNameSchema, 
        db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    channel = _get_owned_channel(db_session, user_id)

    conflict = db_session.exec(
        select(Channel).where(Channel.name == data.name, Channel.id != channel.id)
    ).first()

    if conflict:
        raise HTTPException(
            status.HTTP_409_CONFLICT, 
            "Channel name is already taken."
        )

    channel.name = data.name
    db_session.add(channel)
    db_session.commit()
    db_session.refresh(channel)

    return ApiResponse(
        status=ResponseStatusType.SUCCESS, 
        message="Channel name updated.", 
        data={"name": channel.name}
    )


async def handle_update_description(
    request: Request, 
    data: UpdateDescriptionSchema, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    channel = _get_owned_channel(db_session, user_id)

    channel.description = data.description
    db_session.add(channel)
    db_session.commit()

    return ApiResponse(status=ResponseStatusType.SUCCESS, message="Description updated.", data=None)


async def handle_delete_channel(
    request: Request, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    channel = _get_owned_channel(db_session, user_id)

    db_session.delete(channel)
    db_session.commit()

    return ApiResponse(
        status=ResponseStatusType.SUCCESS, 
        message="Channel deleted.", 
        data=None
    )


async def handle_follow_channel(
    request: Request, 
    channel_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    channel = db_session.get(Channel, channel_id)

    if channel is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Channel not found."
        )

    if channel.user_id == user_id:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "You can't follow your own channel."
        )

    existing = db_session.exec(
        select(Follower).where(
            Follower.follower_id == user_id,
            Follower.channel_id == channel_id,
        )
    ).first()

    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, 
            "You already follow this channel."
        )

    db_session.add(Follower(
        id = uuid.uuid4().hex, 
        follower_id = user_id, 
        channel_id = channel_id
    ))

    try:
        db_session.commit()

    except IntegrityError:
        db_session.rollback()

        raise HTTPException(
            status.HTTP_409_CONFLICT, 
            "You already follow this channel."
        )

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Channel followed.",
        data = {"channel_id": channel_id},
    )


async def handle_unfollow_channel(
    request: Request, 
    channel_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    follow = db_session.exec(
        select(Follower).where(
            Follower.follower_id == user_id,
            Follower.channel_id == channel_id,
        )
    ).first()

    if follow is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "You are not following this channel."
        )

    db_session.delete(follow)
    db_session.commit()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Channel unfollowed.",
        data = {"channel_id": channel_id},
    )
