from pydantic import BaseModel, Field as PydField


class WriteCommentSchema(BaseModel):
    comment: str = PydField(min_length=1, max_length=1000)
