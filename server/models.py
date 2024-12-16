from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core import PydanticCustomError

class CValueError(PydanticCustomError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message)

class GetUserRequestModel(BaseModel):
    user_id: int

    @field_validator("user_id")
    def check_user_id(cls, v):
        if v <= 0:
            raise CValueError("value_error", "User ID must be positive")
        return v

class ListUsersRequestModel(BaseModel):
    page: int = 1
    page_size: int = 10

    @field_validator("page")
    def validate_page(cls, v):
        if v < 1:
            raise CValueError("value_error", "Page must be >= 1")
        return v

    @field_validator("page_size")
    def validate_page_size(cls, v):
        if v <= 0:
            raise CValueError("value_error", "Page size must be > 0")
        return v

class InsertUserRequestModel(BaseModel):
    username: str
    email: EmailStr  # Using EmailStr for built-in validation

    @field_validator("username")
    def username_not_empty(cls, v):
        if not v.strip():
            raise CValueError("value_error", "Username cannot be empty")
        return v