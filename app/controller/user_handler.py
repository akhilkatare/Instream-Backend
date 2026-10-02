from fastapi import (
    status, 
    File, 
    Request, 
    Depends, 
    Response,
    UploadFile, 
    HTTPException, 
)

from app.schemas import (
    ApiResponse, 
    ChangePasswordSchema, 
    DeleteAccountSchema
)

from sqlmodel import Session
from redis.asyncio import Redis

from app.models.user_model import User
from app.types import ResponseStatusType

from app.configs.db import get_db_session
from app.configs.rediss import get_redis_client

from app.utils import password, revocation, token


MAX_DP_BYTES = 2 * 1024 * 1024
ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
REFRESH_TTL_SECONDS = token.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


async def handle_get_user(
    user_id: str,
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user = db_session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "User not found."
        )

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "User fetched.",
        data = {
            "id": user.id,
            "email": user.email,
            "is_streamer": user.is_streamer,
            "has_display_picture": user.display_picture is not None,
            "joined_on": user.joined_on,
        },
    )


async def handle_get_display_picture(
    user_id: str, 
    db_session: Session = Depends(get_db_session)
) -> Response:
    user = db_session.get(User, user_id)
    if user is None or not user.display_picture:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "No display picture."
        )

    return Response(
        content = user.display_picture,
        media_type = "image/jpeg",
        headers = {"Cache-Control": "public, max-age=86400"},
    )


async def handle_upload_dp(
    request: Request, 
    file: UploadFile = File(...), 
    db_session: Session = Depends(get_db_session)
) -> ApiResponse:
    user_id = request.state.user_id

    # 1. Validate type
    if file.content_type not in ALLOWED_IMAGE_TYPES:
        raise HTTPException(
            status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, 
            "Only JPEG, PNG, or WebP images are allowed."
        )

    # 2. Read and size-check
    data = await file.read()
    if len(data) > MAX_DP_BYTES:
        raise HTTPException(
            status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            "Image must be under 2 MB."
        )

    # 3. Store on the user
    user = db_session.get(User, user_id)
    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "User not found."
        )

    user.display_picture = data
    db_session.add(user)
    db_session.commit()

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Display picture updated.",
        data = None
    )


async def handle_change_password(
    request: Request, 
    data: ChangePasswordSchema, 
    db_session: Session = Depends(get_db_session), 
    reds: Redis = Depends(get_redis_client)
) -> ApiResponse:
    user_id = request.state.user_id
    user = db_session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "User not found."
        )

    # 1. SSO accounts have no password to change
    if not user.password:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "This account uses social login; there's no password to change."
        )

    # 2. Verify the current password
    if not password.verify_password(data.old_password, user.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Current password is incorrect."
        )

    # 3. Validate the new password against the rules
    violations = password.validate_password(data.new_password)
    if violations:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY, 
            f"Password must contain: {', '.join(violations)}."
        )

    # 4. New must differ from old
    if password.verify_password(data.new_password, user.password):
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "New password must be different from the current one."
        )

    # 5. Hash and save
    user.password = password.hash_password(data.new_password)
    db_session.add(user)
    db_session.commit()

    # 5. Revoke all existing sessions so other devices must log in again
    await revocation.revoke_all_user_sessions(reds, user_id)

    new_access = token.create_access_token(user_id)
    new_refresh = token.create_refresh_token(user_id)
    refresh_payload = token.decode_token(new_refresh)

    await reds.setex(
        f"refresh:{refresh_payload['jti']}", 
        REFRESH_TTL_SECONDS, 
        user_id
    )

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Password changed.",
        data = {
            "access_token": new_access, 
            "refresh_token": new_refresh, 
            "token_type": "bearer"
        },
    )


async def handle_delete_account(
    request: Request, 
    data: DeleteAccountSchema,
    db_session: Session = Depends(get_db_session), 
    reds: Redis = Depends(get_redis_client)
) -> ApiResponse:
    user_id = request.state.user_id
    user = db_session.get(User, user_id)

    if user is None:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "User not found."
        )

    # Require password confirmation (skip for SSO accounts, which have none)
    if user.password and not password.verify_password(data.password, user.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Password is incorrect."
        )

    # Delete the account
    db_session.delete(user)
    db_session.commit()

    # Revoke all sessions/tokens for this user
    await revocation.revoke_all_user_sessions(reds, user_id)

    return ApiResponse(
        status = ResponseStatusType.SUCCESS, 
        message = "Account deleted.", 
        data = None
    )
