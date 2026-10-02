from app.controller.channel_handler import (
    handle_view_channel,
    handle_get_following,
    handle_create_channel, 
    handle_get_my_channel, 
    handle_follow_channel, 
    handle_delete_channel, 
    handle_unfollow_channel,
    handle_update_description, 
    handle_update_channel_name,
)

from fastapi import APIRouter, Depends
from app.dependencies.security import security
from app.schemas.api_response_schema import ApiResponse


router = APIRouter(prefix = "/channel", tags = ["Channels"])


router.add_api_route(
    "/create", 
    handle_create_channel, 
    methods=["POST"], 
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/view/{channel_id}",
    handle_view_channel,
    methods=["GET"],
    response_model=ApiResponse,
    dependencies=[Depends(security)],
)

router.add_api_route(
    "/following",
    handle_get_following,
    methods=["GET"],
    response_model=ApiResponse,
    dependencies=[Depends(security)],
)


router.add_api_route(
    "/me", 
    handle_get_my_channel, 
    methods=["GET"], 
    response_model=ApiResponse, 
    dependencies=[Depends(security)]
)


router.add_api_route(
    "/update/name", 
    handle_update_channel_name, 
    methods=["PATCH"], 
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/update/description", 
    handle_update_description, 
    methods=["PATCH"], 
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/delete", 
    handle_delete_channel, 
    methods=["DELETE"], 
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/follow/{channel_id}",
    handle_follow_channel,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/unfollow/{channel_id}",
    handle_unfollow_channel,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)
