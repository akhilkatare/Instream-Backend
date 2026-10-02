from pydantic import BaseModel, field_validator, model_validator, EmailStr


class ForgotPasswordSchema(BaseModel):
    email: EmailStr


class ResetPasswordSchema(BaseModel):
    email: EmailStr
    otp: str
    new_password: str
    

class RegisterSchemaEmail(BaseModel):
    email: str
    password: str
    confirm_password: str


    @model_validator(mode="after")
    def passwords_match(self):
        if self.password != self.confirm_password:
            raise ValueError("Password and confirm password do not match.")
        return self


    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class LoginSchemaEmail(BaseModel):
    email: str
    password: str


    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.strip().lower()


class LogoutSchema(BaseModel):
    refresh_token: str


class RefreshSchema(BaseModel):
    refresh_token: str