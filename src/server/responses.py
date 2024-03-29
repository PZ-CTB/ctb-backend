from typing import Union

from flask import Response, make_response

from .database import Message


class Responses:
    """All HTTP responses used in the project."""

    @staticmethod
    def balance(usd_balance: float, btc_balance: float) -> Response:
        """200: returning balance of a user."""
        return make_response(
            {"wallet_usd": usd_balance, "wallet_btc": btc_balance},
            200,
        )

    @staticmethod
    def successfully_deposited() -> Response:
        """200: successfully deposited."""
        return make_response(
            {"message": "Made a successful deposit"},
            200,
        )

    @staticmethod
    def successfully_withdrawn() -> Response:
        """200: successfully withdrawn."""
        return make_response(
            {"message": "Made a successful withdrawal"},
            200,
        )

    @staticmethod
    def successfully_bought() -> Response:
        """200: successfully bought BTC."""
        return make_response(
            {"message": "Successful purchase"},
            200,
        )

    @staticmethod
    def successfully_sold() -> Response:
        """200: successfully sold BTC."""
        return make_response(
            {"message": "Successful sale"},
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
    def chart(filtered_list: list[dict]) -> Response:
        """200: success on chart endpoint."""
        return make_response(filtered_list)

    @staticmethod
    def transaction_history(transactions: list[dict[str, Union[str, float]]]) -> Response:
        """200: /history endpoint response."""
        return make_response(
            {"transactions": transactions},
            200,
        )

    @staticmethod
    def price(price: float) -> Response:
        """200: successfully retrieved current BTC price."""
        return make_response({"price": price}, 200)

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
    def passwords_dont_match_error() -> Response:
        """400: password and confirmPassword don't match."""
        return make_response(
            {"message": "Passwords don't match"},
            400,
        )

    @staticmethod
    def chart_missing_parameters_error() -> Response:
        """400: missing parameters in chart endpoint."""
        return make_response(
            {"message": "Please provide both from and to parameters!"},
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
    def not_enough_money_to_withdraw() -> Response:
        """409: user tried to withdraw more money than they have."""
        return make_response(
            {"message": "Provided amount is greater than user's wallet balance"},
            409,
        )

    @staticmethod
    def not_enough_money_to_make_a_purchase() -> Response:
        """409: user tried to make a purchase without sufficient funds."""
        return make_response(
            {
                "message": "Total price of attempted transaction is greater than user's wallet balance"
            },
            409,
        )

    @staticmethod
    def not_enough_BTC_to_make_a_sale() -> Response:
        """409: user tried to sell more BTC than they own."""
        return make_response(
            {"message": "Amount of BTC provided is greater than user's wallet balance"},
            409,
        )

    @staticmethod
    def maximum_possible_amount_exceeded() -> Response:
        """409: user tried to perform wallet operation with amount exceeding allowed maximum."""
        return make_response(
            {"message": "Amount in the transaction exceeds possible maximum"},
            409,
        )

    @staticmethod
    def internal_server_error() -> Response:
        """500: generic internal error."""
        return make_response(
            {"message": "Internal server error"},
            500,
        )

    @staticmethod
    def internal_database_error(_message: Message) -> Response:
        """500: database internal error."""
        return make_response(
            {"message": "Internal server error"},
            500,
        )
