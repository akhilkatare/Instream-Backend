from app.controller.history_handler import (
    handle_get_history, 
    handle_append_to_history, 
    handle_delete_from_history
)

from app.schemas import ApiResponse
from fastapi import APIRouter, Depends
from app.dependencies.security import security


router = APIRouter(prefix="/history", tags=["History"])


router.add_api_route(
    "",
    handle_get_history,
    methods=["GET"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/append/{video_id}",
    handle_append_to_history,
    methods=["POST"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)

router.add_api_route(
    "/delete/{video_id}",
    handle_delete_from_history,
    methods=["DELETE"],
    response_model=ApiResponse,
    dependencies=[Depends(security)]
)