import uuid

from datetime import date
from sqlmodel import Session, select
from fastapi import Request, Depends, HTTPException, status

from app.schemas import ApiResponse
from app.models import History, Video

from app.types import ResponseStatusType
from app.configs.db import get_db_session


async def handle_get_history(
    request: Request, 
    db_session: Session = Depends(get_db_session), 
    page: int = 1, 
    limit: int = 20
) -> ApiResponse:
    user_id = request.state.user_id
    offset = (page - 1) * limit

    rows = db_session.exec(
        select(History, Video)
        .join(Video, History.video_id == Video.id)
        .where(History.user_id == user_id)
        .order_by(History.watched_on.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    history = [
        {
            "history_id": h.id,
            "watched_on": h.watched_on,
            "video": video.model_dump(exclude={"video_public_id", "thumbnail_public_id"}),
        }
        for h, video in rows
    ]

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "History fetched.",
        data = {
            "history": history, 
            "page": page, 
            "limit": limit
        },
    )


async def handle_append_to_history(
    request: Request, 
    video_id: str, db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    video = db_session.get(Video, video_id)

    if video is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Video not found."
        )

    # Re-watching updates the existing entry instead of duplicating it
    entry = db_session.exec(
        select(History).where(History.user_id == user_id, History.video_id == video_id)
    ).first()

    if entry:
        entry.watched_on = date.today()
    else:
        entry = History(id=uuid.uuid4().hex, user_id=user_id, video_id=video_id)

    db_session.add(entry)
    db_session.commit()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Added to history.",
        data = {"video_id": video_id},
    )


async def handle_delete_from_history(
    request: Request, 
    video_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id

    entry = db_session.exec(
        select(History).where(History.user_id == user_id, History.video_id == video_id)
    ).first()

    if entry is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "This video is not in your history."
        )

    db_session.delete(entry)
    db_session.commit()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Removed from history.",
        data =  {"video_id": video_id},
    )
