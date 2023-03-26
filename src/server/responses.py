from flask import make_response
from jwt import InvalidTokenError

from .database import Message


def me(uuid: str, email: str, wallet_usd: float, wallet_btc: float):
    """200: /me endpoint response"""
    return make_response(
        {
            "uuid": uuid,
            "email": email,
            "wallet_usd": wallet_usd,
            "wallet_btc": wallet_btc
        },
        200,
    )


def auth_token(token: str):
    """201: returning auth token to user on login or refresh"""
    return make_response(
        {"auth_token": token},
        201,
    )


def successfully_registered():
    """201: successfully registered"""
    return make_response(
        {"message": "Successfully registered"},
        201,
    )


def successfully_logged_out():
    """201: successfully logged out"""
    return make_response(
        {"message": "User is successfully logged out"},
        201,
    )


def user_already_exists():
    """202: can't register as user already exists, login required instead"""
    return make_response(
        {"message": "User already exists"},
        202,
        {"WWW-Authenticate": "User already exists. Please Log in."},
    )


def invalid_json_format():
    """400: json parser could not parse the request"""
    return make_response(
        {"message": "Invalid Json format"},
        400,
    )


def token_missing():
    """401: token was not passed with request"""
    return make_response(
        {"message": "Token is missing"},
        401,
        {"WWW-Authenticate": 'Basic realm ="Token is missing!"'},
    )


def token_revoked():
    """401: token was valid but has been revoked in the past"""
    return make_response(
        {"message": "Token is revoked"},
        401,
        {"WWW-Authenticate": 'Basic realm ="Token is revoked!"'},
    )


def token_invalid(e: InvalidTokenError):
    """401: token is invalid"""
    return make_response(
        {"message": f"Token is invalid: {e}"},
        401,
        {"WWW-Authenticate": 'Basic realm ="Token is invalid!"'},
    )


def token_already_revoked():
    """401: logout useless, as token has already been revoked"""
    return make_response(
        {"message": "Token already revoked"},
        401,
        {"WWW-Authenticate": 'Basic realm ="Token already revoked!"'},
    )


def user_does_not_exist():
    """401: user does not exist"""
    return make_response(
        {"message": "User does not exist"},
        401,
        {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
    )


def could_not_verify():
    """403: user provided wrong password"""
    return make_response(
        {"message": "Could not verify"},
        403,
        {"WWW-Authenticate": 'Basic realm ="Wrong password"'},
    )


def internal_database_error(message: Message):
    """500: DatabaseProvider returned message code other than OK"""
    return make_response(
        {"message": f"Internal error: {message}"},
        500,
    )
