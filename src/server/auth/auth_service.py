import uuid

from flask import Response
from werkzeug.security import check_password_hash, generate_password_hash

from .. import QUERIES, Responses
from ..database import DatabaseProvider, Message
from . import TokenService


class AuthService:
    """Authentication Service class.

    Handles various authentication tasks.
    """

    @staticmethod
    def register(email: str, password: str) -> Response:
        """Register method.

        Args:
            email (str): user`s email,
            password (str): user`s password.

        Returns:
            Response: successfully_registered if register succeed, appropriate error otherwise.

        """
        new_uuid: uuid.UUID = uuid.uuid4()

        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_EMAIL, (email,))
            user_exists: bool = handler().fetchall() != []

        if not handler.success:
            return Responses.internal_database_error(handler.message)

        if user_exists:
            return Responses.user_already_exists()

        with DatabaseProvider.handler() as handler:
            handler().execute(
                QUERIES.INSERT_USER, (str(new_uuid), email, generate_password_hash(password))
            )
        if not handler.success:
            print(f"ERROR: server.auth.auth_service.register(): {handler.message}")
            return Responses.internal_database_error(handler.message)

        return Responses.successfully_registered()

    @staticmethod
    def login(email: str, password: str) -> Response:
        """Login method.

        Args:
            email (str): user`s email,
            password (str): user`s password.

        Returns:
            Response: new auth token if login succeed, appropriate error otherwise.

        """
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_LOGIN_DATA_BY_EMAIL, (email,))
            user_information: list[tuple[str, str, str]] = handler().fetchall()

        if not handler.success:
            return Responses.internal_database_error(handler.message)

        if not user_information:
            return Responses.unauthorized_error()

        user_uuid: str = user_information[0][0]  # uuid
        user_email: str = user_information[0][1]  # email
        user_password: str = user_information[0][2]  # password

        if check_password_hash(user_password, password):
            token = TokenService.get_token(user_uuid, user_email)

            return Responses.auth_token(token)

        return Responses.could_not_verify_error()

    @staticmethod
    def me(user_uuid: str) -> Response:
        """Get user`s info.

        Args:
            user_uuid (str): user`s id.

        Returns:
            Response: user`s info if operation succeed, appropriate error otherwise.

        """
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_DATA_BY_UUID, (user_uuid,))
            user_information: list = handler().fetchall()
            print(f"{user_information=}")
        print(f"{user_information=}")

        if not handler.success:
            return Responses.internal_database_error(handler.message)

        if not user_information:
            return Responses.unauthorized_error()

        email: str = user_information[0][0]
        wallet_usd: float = user_information[0][1]
        wallet_btc: float = user_information[0][2]

        return Responses.me(user_uuid, email, wallet_usd, wallet_btc)

    @staticmethod
    def logout(token: str) -> Response:
        """Logout method.

        Args:
            token (str): user`s token.

        Returns:
            Response: successfully_logged_out if logout succeed, appropriate error otherwise.

        """
        if TokenService.is_token_revoked(token):
            return Responses.unauthorized_error()

        if (message := TokenService.revoke_token(token)) is not Message.OK:
            return Responses.internal_database_error(message)

        return Responses.successfully_logged_out()
