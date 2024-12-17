"""
server/models.py 
"""
from pydantic import BaseModel, field_validator, EmailStr
from pydantic_core import PydanticCustomError

class CValueError(PydanticCustomError):
    def __init__(self, code: str, message: str):
        super().__init__(code, message)

class GetUserRequestModel(BaseModel):
    user_id: int

    @field_validator("user_id")
    def check_user_id(cls, v)-> int | CValueError:
        """
        Validate that the user_id is positive.

        This validator checks if the `user_id` field is greater than 0.
        If the value is less than or equal to 0, it raises a `CValueError`.

        :param v: The value of the user_id field.
        :return: The validated user_id if it is positive.
        :raises CValueError: If user_id is less than or equal to 0.
        """
        if v <= 0:
            raise CValueError("value_error", "User ID must be positive")
        return v

class ListUsersRequestModel(BaseModel):
    page: int = 1
    page_size: int = 10

    @field_validator("page")
    def validate_page(cls, v)-> int | CValueError:
        """
        Validate that the page is greater than or equal to 1.

        This validator checks if the `page` field is greater than or equal to 1.
        If the value is less than 1, it raises a `CValueError`.

        :param v: The value of the page field.
        :return: The validated page if it is greater than or equal to 1.
        :raises CValueError: If page is less than 1.
        """
        if v < 1:
            raise CValueError("value_error", "Page must be >= 1")
        return v

    @field_validator("page_size")
    def validate_page_size(cls, v)-> int | CValueError:
        """
        Validate that the page_size is greater than 0.

        This validator checks if the `page_size` field is greater than 0.
        If the value is less than or equal to 0, it raises a `CValueError`.

        :param v: The value of the page_size field.
        :return: The validated page_size if it is greater than 0.
        :raises CValueError: If page_size is less than or equal to 0.
        """
        if v <= 0:
            raise CValueError("value_error", "Page size must be > 0")
        return v

class InsertUserRequestModel(BaseModel):
    username: str
    email: EmailStr  # Using EmailStr for built-in validation

    @field_validator("username")
    def username_not_empty(cls, v)-> str | CValueError:
        """
        Validate that the username is not empty.

        This validator checks if the `username` field is not empty.
        If the value is empty, it raises a `CValueError`.

        :param v: The value of the username field.
        :return: The validated username if it is not empty.
        :raises CValueError: If username is empty.
        """
        if not v.strip():
            raise CValueError("value_error", "Username cannot be empty")
        return v