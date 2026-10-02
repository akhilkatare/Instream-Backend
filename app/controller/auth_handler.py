import jwt
import json
import uuid
import time

from redis.asyncio import Redis
from sqlmodel import Session, select

from fastapi import Depends, HTTPException, status, BackgroundTasks
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.configs.db import get_db_session
from app.configs.rediss import get_redis_client

from app.schemas import (
    ApiResponse, 
    RegisterSchemaEmail,
    LoginSchemaEmail, 
    VerifyEmailSchema, 
    LogoutSchema, 
    RefreshSchema,
    ForgotPasswordSchema,
    ResetPasswordSchema
)

from app.models.user_model import User
from app.types import ResponseStatusType
from app.utils import password, otp, email_service, token


MAX_OTP_ATTEMPTS = 5
OTP_TTL_SECONDS = 10 * 60 # For 10 mins.
bearer_scheme = HTTPBearer(auto_error=False)
REFRESH_TTL_SECONDS = token.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60


async def handle_refresh_token(
    data: RefreshSchema, 
    reds: Redis = Depends(get_redis_client)
) -> ApiResponse:
    # 1. Decode & validate signature/expiry
    try:
        payload = token.decode_token(data.refresh_token)

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Refresh token expired. Please log in again."
        )
    
    except jwt.InvalidTokenError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Invalid refresh token."
        )

    # 2. Must actually be a refresh token
    if payload.get("type") != "refresh":
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Invalid token type."
        )

    # 3. Must still be whitelisted in Redis.
    old_key = f"refresh:{payload['jti']}"
    user_id = await reds.get(old_key)

    if user_id is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Refresh token has been revoked. Please log in again."
        )

    # 4. Issue a brand new pair
    await reds.delete(old_key)

    new_access = token.create_access_token(user_id)
    new_refresh = token.create_refresh_token(user_id)
    new_payload = token.decode_token(new_refresh)

    await reds.setex(
        f"refresh:{new_payload['jti']}",
        REFRESH_TTL_SECONDS, 
        user_id
    )

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Token refreshed.",
        data = {
            "access_token": new_access,
            "refresh_token": new_refresh,
            "token_type": "bearer",
        },
    )


async def handle_register_email(
    user_data: RegisterSchemaEmail, 
    background_tasks: BackgroundTasks, 
    db_session: Session = Depends(get_db_session), 
    reds: Redis = Depends(get_redis_client)
) -> ApiResponse:
    email = user_data.email.strip()

    # 1. Check whether an account already exists
    existing = db_session.exec(select(User).where(User.email == email)).first()
    if existing:
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "An account with this email already exists.",
        )

    # 2. Guard against a duplicate 'pending' registration in Redis
    if await reds.exists(f"pending_registration:{email}"):
        raise HTTPException(
            status_code = status.HTTP_409_CONFLICT,
            detail = "A verification email was already sent. Please check your inbox.",
        )

    # 3. Validate the password against the rules
    violations = password.validate_password(user_data.password)
    if violations:
        raise HTTPException(
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail = f"Password must contain: {', '.join(violations)}.",
        )

    # 4. Hash the password and store the pending registration in Redis
    otp_code = otp.generate_otp(6)
    payload = json.dumps({
        "email": email,
        "password": password.hash_password(user_data.password),
        "auth_type": "email",
        "otp": otp_code
    })
    await reds.setex(f"pending_registration:{email}", OTP_TTL_SECONDS, payload)

    # 5. Send email.
    background_tasks.add_task(
        email_service.send_otp_email, 
        email, otp_code, 
        OTP_TTL_SECONDS // 60
    )

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Registration received. Check your email to verify your account.",
        data = {"expires_in_seconds": OTP_TTL_SECONDS},
    )


async def handle_verify_email(
    data: VerifyEmailSchema, 
    db_session: Session = Depends(get_db_session), 
    reds: Redis = Depends(get_redis_client)
) -> ApiResponse:
    email = data.email.strip()
    key = f"pending_registration:{email}"

    raw = await reds.get(key)
    if raw is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "Code expired or not found. Please register again."
        )

    # 1. Limit attempts per pending registration
    attempts_key = f"otp_attempts:{email}"
    attempts = await reds.incr(attempts_key)

    if attempts == 1:
        await reds.expire(attempts_key, OTP_TTL_SECONDS)

    if attempts > MAX_OTP_ATTEMPTS:
        await reds.delete(key, attempts_key)

        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS, 
            "Too many attempts. Please register again."
        )

    # 2. Validate the OTP.
    payload = json.loads(raw)
    if data.otp != payload["otp"]:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "Invalid verification code."
        )

    # 3. Create the user account in DB
    user = User(
        id = uuid.uuid4().hex,
        email = payload["email"],
        password = payload["password"],
        auth_type = payload["auth_type"],
    )

    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)

    # 4. Cleanup Redis
    await reds.delete(key, attempts_key)

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Account verified successfully.",
        data = {"user_id": user.id},
    )


async def handle_forgot_password(
    data: ForgotPasswordSchema,
    background_tasks: BackgroundTasks,
    db_session: Session = Depends(get_db_session),
    reds: Redis = Depends(get_redis_client),
) -> ApiResponse:
    email = data.email.strip()
    user = db_session.exec(select(User).where(User.email == email)).first()

    # Only email-auth users have a password to reset (SSO users have none).
    if user and user.password:
        otp_code = otp.generate_otp(6)
        payload = json.dumps({"otp": otp_code})
        await reds.setex(f"password_reset:{email}", OTP_TTL_SECONDS, payload)

        background_tasks.add_task(
            email_service.send_otp_email,
            email, otp_code,
            OTP_TTL_SECONDS // 60,
        )

    # Always success — never reveal whether the email is registered.
    return ApiResponse(
        status=ResponseStatusType.SUCCESS,
        message="If that email exists, a reset code has been sent.",
        data={"expires_in_seconds": OTP_TTL_SECONDS},
    )


async def handle_reset_password(
    data: ResetPasswordSchema,
    db_session: Session = Depends(get_db_session),
    reds: Redis = Depends(get_redis_client),
) -> ApiResponse:
    email = data.email.strip()
    key = f"password_reset:{email}"

    raw = await reds.get(key)
    if raw is None:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Code expired or not found. Please request a new one.",
        )

    attempts_key = f"reset_attempts:{email}"
    attempts = await reds.incr(attempts_key)

    if attempts == 1:
        await reds.expire(attempts_key, OTP_TTL_SECONDS)

    if attempts > MAX_OTP_ATTEMPTS:
        await reds.delete(key, attempts_key)
        raise HTTPException(
            status.HTTP_429_TOO_MANY_REQUESTS,
            "Too many attempts. Please request a new code.",
        )

    # Validate the OTP.
    payload = json.loads(raw)
    if data.otp != payload["otp"]:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "Invalid verification code."
        )

    # Enforce the same password rules as registration.
    violations = password.validate_password(data.new_password)
    if violations:
        raise HTTPException(
            status.HTTP_422_UNPROCESSABLE_ENTITY,
            f"Password must contain: {', '.join(violations)}.",
        )

    user = db_session.exec(select(User).where(User.email == email)).first()
    if not user or not user.password:
        raise HTTPException(
            status.HTTP_404_NOT_FOUND, 
            "Account not found."
        )

    user.password = password.hash_password(data.new_password)
    db_session.add(user)
    db_session.commit()

    await reds.delete(key, attempts_key)

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Password reset. Please log in.",
        data = None,
    )


async def handle_login_email(
    user_data: LoginSchemaEmail, 
    db_session: Session = Depends(get_db_session), 
    reds: Redis = Depends(get_redis_client)
) -> ApiResponse:
    email = user_data.email.strip()
    user = db_session.exec(select(User).where(User.email == email)).first()

    if user is None:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Invalid email or password."
        )
    
    if not user.password:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST, 
            "This account uses social login. Sign in with SSO."
        )
    
    if not password.verify_password(user_data.password, user.password):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Invalid email or password."
        )

    # 3. Issue tokens
    access_token = token.create_access_token(user.id)
    refresh_token = token.create_refresh_token(user.id)

    # Whitelist the refresh token
    refresh_payload = token.decode_token(refresh_token)

    await reds.setex(
        f"refresh:{refresh_payload['jti']}", 
        REFRESH_TTL_SECONDS, 
        user.id
    )

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Login successful.",
        data = {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
        },
    )


async def handle_logout(
    data: LogoutSchema,
    creds: HTTPAuthorizationCredentials = Depends(bearer_scheme),  
    reds: Redis = Depends(get_redis_client)
) -> ApiResponse:
    # 1. Decode the refresh token.
    try:
        payload = token.decode_token(data.refresh_token)

    except jwt.ExpiredSignatureError:
        return ApiResponse(
            status = ResponseStatusType.SUCCESS, 
            message = "Logged out."
        )
    
    except jwt.InvalidTokenError:
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED, 
            "Invalid token."
        )

     # 2. Denylist the access token so it stops working IMMEDIATELY
    if creds is not None:
        try:
            access_payload = token.decode_token(creds.credentials)

            if access_payload.get("type") == "access":
                ttl = access_payload["exp"] - int(time.time())

                if ttl > 0:
                    await reds.setex(
                        f"denylist:{access_payload['jti']}", ttl, "1")

        except jwt.InvalidTokenError:
            pass           

    # 3. Revoke it: delete the whitelist entry.
    await reds.delete(f"refresh:{payload['jti']}")

    return ApiResponse(
        status = ResponseStatusType.SUCCESS,
        message = "Logged out successfully.",
        data = None,
    )
