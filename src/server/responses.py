from enum import Enum
from typing import Callable, Any

from flask import Response, make_response

from .database import Message


def _me(uuid: str, email: str, wallet_usd: float, wallet_btc: float) -> Response:
    """200: /me endpoint response."""
    return make_response(
        {"uuid": uuid, "email": email, "wallet_usd": wallet_usd, "wallet_btc": wallet_btc},
        200,
    )


def _auth_token(token: str) -> Response:
    """201: returning auth token to user on login or refresh."""
    return make_response(
        {"auth_token": token},
        201,
    )


def _successfully_registered() -> Response:
    """201: successfully registered."""
    return make_response(
        {"message": "Successfully registered"},
        201,
    )


def _successfully_logged_out() -> Response:
    """201: successfully logged out."""
    return make_response(
        {"message": "User is successfully logged out"},
        201,
    )


def _user_already_exists() -> Response:
    """202: can't register because user already exists, login required instead."""
    return make_response(
        {"message": "User already exists"},
        202,
        {"WWW-Authenticate": "User already exists"},
    )


def _invalid_json_format() -> Response:
    """400: json parser could not parse the request."""
    return make_response(
        {"message": "Invalid Json format"},
        400,
    )


def _unauthorized() -> Response:
    """401: generic problem with authorization or token."""
    return make_response(
        {"message": "Not authorized to perform this action"},
        401,
        {"WWW-Authenticate", 'Basic realm ="Not authorized to perform this action!"'},
    )


def _could_not_verify() -> Response:
    """403: user provided wrong password."""
    return make_response(
        {"message": "Could not verify"},
        403,
        {"WWW-Authenticate": 'Basic realm ="Wrong password"'},
    )


def _internal_database_error(message: Message) -> Response:
    """500: DatabaseProvider returned message code other than OK."""
    return make_response(
        {"message": f"Internal error: {message}"},
        500,
    )


class RESPONSES(Callable, Enum):
    """All HTTP responses used in the project."""

    ME: Callable = _me
    AUTH_TOKEN: Callable = _auth_token
    SUCCESSFULLY_REGISTERED: Callable = _successfully_registered
    SUCCESSFULLY_LOGGED_OUT: Callable = _successfully_logged_out
    USER_ALREADY_EXISTS: Callable = _user_already_exists
    INVALID_JSON_FORMAT: Callable = _invalid_json_format
    UNAUTHORIZED: Callable = _unauthorized
    COULD_NOT_VERIFY: Callable = _could_not_verify
    INTERNAL_DATABASE_ERROR: Callable = _internal_database_error

    def __call__(self, *args, **kwargs) -> Any:
        """Call the function."""
        self.value(*args, **kwargs)
