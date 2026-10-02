from typing import Optional
from pydantic import BaseModel
from app.types import ResponseStatusType


class ApiResponse(BaseModel):
    status: ResponseStatusType
    data: Optional[dict] = None
    message: Optional[str] = None
