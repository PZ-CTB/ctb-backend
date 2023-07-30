import logging
import os
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable

import jwt
from flask import Response, request

from .. import QUERIES, Responses
from ..database import DatabaseProvider, Message


class TokenService:
    """Token Service class.

    Provides utility methods for token handling.
    """

    _token_expiration_minutes: int = 30
    _secret: str = os.getenv("SECRET_KEY", "secret")
    _algorithms: list[str] = ["HS256"]

    @classmethod
    def token_required(cls, fun: Callable[..., Response]) -> Callable[..., Response]:
        """Validate received token."""

        @wraps(fun)
        def decorated(*args: tuple, **kwargs: dict) -> Response:
            token: str = ""
            # JWT is passed in the request header
            if "x-access-token" in request.headers:
                token = request.headers["x-access-token"]

            # If the token is missing or revoked passed return message and exit function
            if not token or cls.is_token_revoked(token):
                return Responses.unauthorized_error()

            # Decode the token and retrieve the information contained in it
            try:
                data: dict[str, Any] = jwt.decode(token, cls._secret, algorithms=cls._algorithms)
            except jwt.InvalidTokenError as e:
                logging.error(f"{e=}")
                return Responses.unauthorized_error()

            user_uuid: str = data["uuid"]

            with DatabaseProvider.handler() as handler:
                handler().execute(QUERIES.SELECT_USER_UUID, (user_uuid,))
                response = handler().fetchall()
            if not handler.success:
                return Responses.internal_database_error(handler.message)
            user_exists: bool = response != []

            if not user_exists:
                return Responses.unauthorized_error()

            # Returns the current logged-in users context to the routes
            return fun(user_uuid, token, *args, **kwargs)

        return decorated

    @classmethod
    def revoke_token(cls, token: str) -> Message:
        """Revoke activated token.

        Args:
            token (str): token to revoke.

        Returns:
            Message: message returned by database handler.

        """
        decoded_token: dict[str, Any] = jwt.decode(token, cls._secret, algorithms=cls._algorithms)
        expiry: datetime = datetime.fromtimestamp(decoded_token["exp"])

        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.INSERT_REVOKED_TOKEN, (token, expiry))
        return handler.message

    @classmethod
    def is_token_revoked(cls, token: str) -> bool:
        """Check if token is revoked.

        Args:
            token (str): token to check.

        Returns:
            Message: True if token is revoked, False otherwise.

        """
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_REVOKED_TOKEN, (token, datetime.utcnow()))
            is_revoked: bool = handler().fetchall() != []
        if not handler.success:
            return True
        return is_revoked

    @classmethod
    def get_token(cls, user_uuid: str, email: str) -> str:
        """Create and return new token.

        Args:
            user_uuid (str): user`s id,
            email (str): user`s email.

        Returns:
            str: new token.

        """
        return jwt.encode(
            {
                "uuid": user_uuid,
                "email": email,
                "exp": datetime.utcnow() + timedelta(minutes=cls._token_expiration_minutes),
            },
            cls._secret,
        )

    @classmethod
    def refresh(cls, user_uuid: str, token: str) -> Response:
        """Refresh token.

        Args:
            user_uuid (str): user`s id,
            token (str): user`s token.

        Returns:
            Response: new token if succeed, appropriate error otherwise.

        """
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_EMAIL_BY_UUID, (user_uuid,))
            user_information: list[tuple[str]] = handler().fetchall()

        if not handler.success:
            return Responses.internal_database_error(handler.message)

        if not user_information:
            return Responses.unauthorized_error()

        user_email: str = user_information[0][0]

        new_token: str = cls.get_token(user_uuid, user_email)

        revoke_result: Message = cls.revoke_token(token)
        if revoke_result is not Message.OK:
            return Responses.internal_database_error(revoke_result)

        return Responses.auth_token(new_token)
