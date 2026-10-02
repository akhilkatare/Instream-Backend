from pydantic import BaseModel, field_validator


class VerifyEmailSchema(BaseModel):
    email: str
    otp: str


    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()