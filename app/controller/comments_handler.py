import uuid

from sqlmodel import Session, select
from fastapi import Request, Depends, HTTPException, status

from app.types import ResponseStatusType
from app.configs.db import get_db_session

from app.models import Comment, Video, Channel, User
from app.schemas import ApiResponse, WriteCommentSchema


async def handle_write_comment(
    request: Request, 
    video_id: str, data: WriteCommentSchema, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    video = db_session.get(Video, video_id)

    if video is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Video not found."
        )

    comment = Comment(
        id = uuid.uuid4().hex,
        video_id = video_id,
        sender_id = user_id,
        comment = data.comment,
    )

    db_session.add(comment)
    db_session.commit()
    db_session.refresh(comment)

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Comment posted.",
        data = {
            "comment_id": comment.id, 
            "comment": comment.comment, 
            "commented_at": comment.commented_at
        },
    )


async def handle_get_comments(
    video_id: str, 
    db_session: Session = Depends(get_db_session), 
    page: int = 1, 
    limit: int = 20
) -> ApiResponse:
    offset = (page - 1) * limit

    rows = db_session.exec(
        select(Comment, User)
        .join(User, Comment.sender_id == User.id)
        .where(Comment.video_id == video_id)
        .order_by(Comment.commented_at.desc())
        .offset(offset)
        .limit(limit)
    ).all()

    comments = [
        {
            "id": c.id,
            "comment": c.comment,
            "commented_at": c.commented_at,
            "sender": {
                "id": u.id, 
                "email": u.email,
            "has_display_picture": u.display_picture is not None,
            },
        }
        for c, u in rows
    ]

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Comments fetched.",
        data = {
            "comments": comments, 
            "page": page, 
            "limit": limit
        },
    )


async def handle_delete_comment(
    request: Request, 
    comment_id: str, 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id
    comment = db_session.get(Comment, comment_id)

    if comment is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Comment not found."
        )

    # Author can delete their own comment; the channel owner can delete any comment on their video
    if comment.sender_id != user_id:
        video = db_session.get(Video, comment.video_id)
        channel = db_session.get(Channel, video.channel_id) if video else None

        if not channel or channel.user_id != user_id:
            raise HTTPException(
                status.HTTP_403_FORBIDDEN, 
                "You can't delete this comment."
            )

    db_session.delete(comment)
    db_session.commit()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Comment deleted.",
        data = {"comment_id": comment_id},
    )
