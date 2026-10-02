import uuid

from app.models import (
    User, 
    Like, 
    Video, 
    Channel, 
    Follower
)

from sqlalchemy.exc import IntegrityError
from sqlmodel import Session, select, func

from fastapi import Request, Depends, HTTPException, status

from app.utils import cloudinary_service
from app.configs.db import get_db_session

from app.types import ResponseStatusType
from app.schemas import CreateVideoSchema, ApiResponse


def _like_count():
    return (
        select(func.count(Like.id))
        .where(Like.video_id == Video.id)
        .correlate(Video)
        .scalar_subquery()
    )


def _serialize(rows):
    return [
        {**v.model_dump(), "likes": likes}
        for v, likes in rows
    ]


async def handle_get_videos(
    db_session: Session = Depends(get_db_session), 
    page: int = 1, 
    limit: int = 20
) -> ApiResponse:
    offset = (page - 1) * limit

    rows = db_session.exec(
        select(Video, _like_count())
        .order_by(Video.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS, 
        message = "Videos fetched.", 
        data = {"videos": _serialize(rows)}
    )


async def handle_search_videos(
    query: str, 
    db_session: Session = Depends(get_db_session), 
    page: int = 1, 
    limit: int = 20
) -> ApiResponse:
    offset = (page - 1) * limit

    rows = db_session.exec(
        select(Video, _like_count())
        .where(Video.title.ilike(f"%{query}%") | Video.description.ilike(f"%{query}%"))
        .order_by(Video.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS, 
        message = "Search results.", 
        data = {"videos": _serialize(rows)}
    )


async def handle_get_channel_videos(
    channel_id: str, 
    db_session: Session = Depends(get_db_session), 
    page: int = 1, 
    limit: int = 20
) -> ApiResponse:
    channel = db_session.get(Channel, channel_id)
    if channel is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Channel not found."
        )

    offset = (page - 1) * limit

    rows = db_session.exec(
        select(Video, _like_count())
        .where(Video.channel_id == channel_id)
        .order_by(Video.uploaded_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Channel videos fetched.",
        data = {"videos": _serialize(rows)},
    )


async def handle_get_video(
    request: Request, 
    video_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    video = db_session.get(Video, video_id)
    if video is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Video not found."
        )

    like_count = db_session.exec(
        select(func.count(Like.id)).where(Like.video_id == video_id)
    ).one()

    user_id = getattr(request.state, "user_id", None)

    is_liked = False
    if user_id:
        is_liked = db_session.exec(
            select(Like.id).where(Like.user_id == user_id, Like.video_id == video_id)
        ).first() is not None

    # Channel block with its own follower count + is_following
    channel = db_session.get(Channel, video.channel_id)
    channel_data = None

    if channel:
        followers_count = db_session.exec(
            select(func.count(Follower.id)).where(Follower.channel_id == channel.id)
        ).one()

        is_following = False

        if user_id:
            is_following = db_session.exec(
                select(Follower.id).where(
                    Follower.follower_id == user_id, Follower.channel_id == channel.id
                )
            ).first() is not None

        channel_data = {
            "id": channel.id,
            "name": channel.name,
            "followers": followers_count,
            "is_following": is_following,
        }

    return ApiResponse(
        status=ResponseStatusType.SUCCESS,
        message="Video fetched.",
        data={
            **video.model_dump(),
            "likes": like_count,
            "is_liked": is_liked,
            "channel": channel_data,
        },
    )


async def handle_generate_signatures(
    request: Request, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user = db_session.get(User, request.state.user_id)
    if not user or not user.is_streamer:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, 
            "Only streamers can upload videos."
        )

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Upload signatures generated.",
        data = cloudinary_service.generate_upload_signatures(),
    )


async def handle_metadata_upload(
    request: Request, 
    data: CreateVideoSchema, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    channel = db_session.exec(select(Channel).where(Channel.user_id == user_id)).first()

    if not channel:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, 
            "You need a channel to publish videos."
        )

    video = Video(
        id = uuid.uuid4().hex,
        channel_id = channel.id,
        title = data.title,
        description = data.description,
        duration = data.duration,
        video_url = data.video_url,
        video_public_id = data.video_public_id,
        thumbnail_url = data.thumbnail_url,
        thumbnail_public_id = data.thumbnail_public_id,
    )

    db_session.add(video)
    db_session.commit()
    db_session.refresh(video)

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Video published.",
        data = {
            "video_id": video.id, 
            "title": video.title
        },
    )


async def handle_delete_video(
    request: Request, 
    video_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    video = db_session.get(Video, video_id)
    if not video:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Video not found."
        )

    channel = db_session.get(Channel, video.channel_id)
    if not channel or channel.user_id != user_id:
        raise HTTPException(
            status.HTTP_403_FORBIDDEN, 
            "You can only delete your own videos."
        )

    await cloudinary_service.destroy_asset(video.video_public_id, "video")
    await cloudinary_service.destroy_asset(video.thumbnail_public_id, "image")

    db_session.delete(video)
    db_session.commit()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Video deleted.",
        data = {"video_id": video_id},
    )


async def handle_like_video(
    request: Request, 
    video_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    video = db_session.get(Video, video_id)
    if not video:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Video not found."
        )

    existing = db_session.exec(
        select(Like).where(Like.user_id == user_id, Like.video_id == video_id)
    ).first()

    if existing:
        raise HTTPException(
            status.HTTP_409_CONFLICT, 
            "You already liked this video."
        )

    db_session.add(Like(
        id = uuid.uuid4().hex, 
        user_id = user_id, 
        video_id = video_id
    ))

    try:
        db_session.commit()

    except IntegrityError:
        db_session.rollback()

        raise HTTPException(
            status.HTTP_409_CONFLICT, 
            "You already liked this video."
        )

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Video liked.",
        data = {"video_id": video_id},
    )



async def handle_unlike_video(
    request: Request, 
    video_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id

    like = db_session.exec(
        select(Like).where(Like.user_id == user_id, Like.video_id == video_id)
    ).first()

    if like is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "You haven't liked this video."
        )

    db_session.delete(like)
    db_session.commit()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Video unliked.",
        data = {"video_id": video_id},
    )


async def handle_increment_views(
    video_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    video = db_session.get(Video, video_id)
    if video is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND,
            "Video not found."
        )

    video.views = Video.views + 1
    db_session.add(video)
    db_session.commit()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "View counted.",
        data = {"video_id": video_id},
    )
