from pydantic import Field

from app.schemas.base import BaseSchema


class RefreshTokenRequest(BaseSchema):
    refresh_token: str = Field(..., min_length=10, max_length=255)


class TokenResponse(BaseSchema):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    must_change_password: bool = False


class MFASetupResponse(BaseSchema):
    secret: str
    otpauth_uri: str


class MFAVerifyRequest(BaseSchema):
    code: str = Field(..., min_length=6, max_length=6, pattern=r"^\d{6}$")
