from app.controller.video_handler import (
    handle_get_video,
    handle_get_videos, 
    handle_like_video, 
    handle_delete_video, 
    handle_unlike_video, 
    handle_search_videos, 
    handle_increment_views, 
    handle_metadata_upload,
    handle_get_channel_videos, 
    handle_generate_signatures, 
)

from app.schemas import ApiResponse
from fastapi import APIRouter, Depends
from app.dependencies.security import security


router = APIRouter(prefix = "/video", tags=["Videos"])


router.add_api_route(
    "",
    handle_get_videos,
    methods = ["GET"],
    response_model = ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/search",
    handle_search_videos,
    methods = ["GET"],
    response_model = ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/{video_id}",
    handle_get_video,
    methods=["GET"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/channel-videos/{channel_id}",
    handle_get_channel_videos,
    methods=["GET"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/upload/generate-signatures",
    handle_generate_signatures,
    methods = ["POST"],
    response_model = ApiResponse,
    dependencies = [Depends(security)]
)

router.add_api_route(
    "/upload/data",
    handle_metadata_upload,
    methods = ["POST"],
    response_model = ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/delete",
    handle_delete_video,
    methods = ["DELETE"],
    response_model = ApiResponse,
    dependencies = [Depends(security)]
)

router.add_api_route(
    "/like/{video_id}",
    handle_like_video,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/unlike/{video_id}",
    handle_unlike_video,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/inc-views",
    handle_increment_views,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)