from app.controller.user_handler import (
    handle_get_user, 
    handle_upload_dp, 
    handle_delete_account, 
    handle_change_password, 
    handle_get_display_picture,
)

from app.schemas import ApiResponse
from fastapi import APIRouter, Depends
from app.dependencies.security import security


router = APIRouter(prefix = "/account", tags=["Account"])


router.add_api_route(
    "/{user_id}",
    handle_get_user,
    methods=["GET"],
    response_model=ApiResponse,
)

router.add_api_route(
    "/{user_id}/display-picture",
    handle_get_display_picture,
    methods=["GET"],
)

router.add_api_route(
    "/upload-dp",
    handle_upload_dp,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)],
)

router.add_api_route(
    "/change-password",
    handle_change_password,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)],
)

router.add_api_route(
    "/delete",
    handle_delete_account,
    methods=["DELETE"],
    response_model=ApiResponse,
    dependencies=[Depends(security)],
)