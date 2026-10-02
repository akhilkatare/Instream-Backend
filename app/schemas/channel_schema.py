from pydantic import BaseModel, Field


class CreateChannelSchema(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    description: str = Field(max_length=1000)


class UpdateChannelNameSchema(BaseModel):
    name: str = Field(min_length=3, max_length=50)
    

class UpdateDescriptionSchema(BaseModel):
    description: str = Field(max_length=1000)
