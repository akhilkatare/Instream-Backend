from enum import Enum


class ResponseStatusType(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"
