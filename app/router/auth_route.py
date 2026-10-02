from app.controller.auth_handler import (
    handle_logout,
    handle_login_email,
    handle_verify_email,
    handle_refresh_token,
    handle_register_email,
    handle_reset_password,
    handle_forgot_password,
)

from fastapi import APIRouter, Depends
from app.dependencies.rate_limiter import RateLimiter
from app.schemas.api_response_schema import ApiResponse


router = APIRouter(prefix="/auth", tags=["Auth"])


router.add_api_route(
    "/refresh", 
    handle_refresh_token, 
    methods=["POST"], 
    response_model=ApiResponse
)

router.add_api_route(
    "/register/email", 
    handle_register_email, 
    methods=["POST"], 
    response_model=ApiResponse
)

router.add_api_route(
    "/verify/email", 
    handle_verify_email, 
    methods=["POST"], 
    response_model=ApiResponse,
    dependencies=[Depends(RateLimiter(max_requests=10, window_seconds=60))]
)

router.add_api_route(
    "/login/email", 
    handle_login_email, 
    methods=["POST"], 
    response_model=ApiResponse,
    dependencies=[Depends(RateLimiter(max_requests=10, window_seconds=60))]
)

router.add_api_route(
    "/forgot-password/email", 
    handle_forgot_password, 
    methods=["POST"], 
    response_model=ApiResponse
)

router.add_api_route(
    "/reset-password/email", 
    handle_reset_password, 
    methods=["POST"], 
    response_model=ApiResponse
)

router.add_api_route(
    "/logout", 
    handle_logout, 
    methods=["POST"], 
    response_model=ApiResponse
)
