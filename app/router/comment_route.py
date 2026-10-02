from app.controller.comments_handler import (
    handle_get_comments, 
    handle_write_comment, 
    handle_delete_comment
)

from app.schemas import ApiResponse
from fastapi import APIRouter, Depends
from app.dependencies.security import security


router = APIRouter(prefix="/comment", tags=["Comment"])


router.add_api_route(
    "/write/{video_id}",
    handle_write_comment,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/{video_id}",
    handle_get_comments,
    methods=["GET"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/delete/{comment_id}",
    handle_delete_comment,
    methods=["DELETE"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)