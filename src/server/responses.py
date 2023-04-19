from flask import Response, make_response

from .database import Message


class Responses:
    """All HTTP responses used in the project."""

    @staticmethod
    def successfully_deposited() -> Response:
        """200: successfully deposited."""
        return make_response(
            {"message": "Made a successful deposit"},
            200,
        )

    @staticmethod
    def me(uuid: str, email: str, wallet_usd: float, wallet_btc: float) -> Response:
        """200: /me endpoint response."""
        return make_response(
            {"uuid": uuid, "email": email, "wallet_usd": wallet_usd, "wallet_btc": wallet_btc},
            200,
        )

    @staticmethod
    def auth_token(token: str) -> Response:
        """201: returning auth token to user on login or refresh."""
        return make_response(
            {"auth_token": token},
            201,
        )

    @staticmethod
    def successfully_registered() -> Response:
        """201: successfully registered."""
        return make_response(
            {"message": "Successfully registered"},
            201,
        )

    @staticmethod
    def successfully_logged_out() -> Response:
        """201: successfully logged out."""
        return make_response(
            {"message": "User is successfully logged out"},
            201,
        )

    @staticmethod
    def user_already_exists() -> Response:
        """202: can't register because user already exists, login required instead."""
        return make_response(
            {"message": "User already exists"},
            202,
            {"WWW-Authenticate": "User already exists"},
        )

    @staticmethod
    def invalid_json_format_error() -> Response:
        """400: json parser could not parse the request."""
        return make_response(
            {"message": "Invalid Json format"},
            400,
        )

    @staticmethod
    def unauthorized_error() -> Response:
        """401: generic problem with authorization or token."""
        return make_response(
            {"message": "Not authorized to perform this action"},
            401,
            {"WWW-Authenticate": 'Basic realm ="Not authorized to perform this action!"'},
        )

    @staticmethod
    def could_not_verify_error() -> Response:
        """403: user provided wrong password."""
        return make_response(
            {"message": "Could not verify"},
            403,
            {"WWW-Authenticate": 'Basic realm ="Wrong password"'},
        )

    @staticmethod
    def invalid_amount() -> Response:
        """409: user provided invalid amount of money."""
        return make_response(
            {"message": "Amount must be greater than 0"},
            409,
        )

    @staticmethod
    def internal_database_error(_message: Message) -> Response:
        """500: generic internal error."""
        return make_response(
            {"message": "Internal server error"},
            500,
        )
