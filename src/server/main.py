import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable
from uuid import UUID

import jwt
from flask import Flask, Response, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from . import QUERIES, responses
from .database import DatabaseProvider, Message

DatabaseProvider.initialize()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000/", "https://ctb-agh.netlify.app/"])
# Generation method -> uuid.uuid4().hex
app.config["SECRET_KEY"] = "55cfba6d5bd6405c8e9b7b681f6b8835"


def token_required(fun: Callable[..., Response]) -> Callable[..., Response]:
    """Validate received token."""

    @wraps(fun)
    def decorated(*args: tuple, **kwargs: dict) -> Response:
        """Validate received token."""
        token: str = ""
        # JWT is passed in the request header
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]

        # If the token is not passed return message and exit function
        if not token:
            return responses.token_missing()

        # If the token is revoked return message and exit function
        if is_token_revoked(token):
            return responses.token_revoked()

        # Decode the token and retrieve the information contained in it
        try:
            data: dict[str, Any] = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.InvalidTokenError as e:
            return responses.token_invalid(e)

        user_uuid: str = data["uuid"]

        with DatabaseProvider.query(QUERIES.SELECT_USER_UUID, (user_uuid,)) as response:
            if response.message is not Message.OK:
                return responses.internal_database_error(response.message)
            user_exists: bool = response.data != []

        if not user_exists:
            return responses.user_does_not_exist()

        # Returns the current logged-in users context to the routes
        return fun(user_uuid, token, *args, **kwargs)

    return decorated


def revoke_token(token: str) -> Message:
    """Revoking activated token."""
    decoded_token: dict[str, Any] = jwt.decode(
        token, app.config["SECRET_KEY"], algorithms=["HS256"]
    )
    expiry: datetime = datetime.fromtimestamp(decoded_token["exp"])

    with DatabaseProvider.query(QUERIES.INSERT_REVOKED_TOKEN, (token, expiry)) as response:
        return response.message


def is_token_revoked(token: str) -> bool:
    """Check if token is revoked."""
    with DatabaseProvider.query(
        QUERIES.SELECT_REVOKED_TOKEN,
        (
            token,
            datetime.utcnow(),
        ),
    ) as response:
        if response.message is not Message.OK:
            return True
        is_revoked: bool = response.data != []
        return is_revoked


@app.route("/register", methods=["POST"])
def register() -> Response:
    """Registration endpoint."""
    new_user: dict[str, str] = request.get_json()

    unique_id: UUID = uuid.uuid4()
    email: str = new_user.get("email", "")
    password: str = new_user.get("password", "")

    if not email or not password:
        return responses.invalid_json_format()

    with DatabaseProvider.query(QUERIES.SELECT_USER_EMAIL, (email,)) as response:
        if response.message is not Message.OK:
            return responses.internal_database_error(response.message)

        user_exists: bool = response.data != []

    if user_exists:
        return responses.user_already_exists()

    with DatabaseProvider.query(
        QUERIES.INSERT_USER,
        (str(unique_id), email, generate_password_hash(password)),
    ) as response:
        if response.message is not Message.OK:
            print(f"ERROR: server.register(): {response.message}")
            return responses.internal_database_error(response.message)

    return responses.successfully_registered()


@app.route("/login", methods=["POST"])
def login() -> Response:
    """Login endpoint."""
    auth: dict[str, Any] = request.get_json()

    email: str = auth.get("email", "")
    password: str = auth.get("password", "")

    if not email or not password:
        return responses.invalid_json_format()

    with DatabaseProvider.query(QUERIES.SELECT_USER_LOGIN_DATA_BY_EMAIL, (email,)) as response:
        if response.message is not Message.OK:
            return responses.internal_database_error(response.message)

        user_information: list[tuple[str, str, str]] = response.data

    if not user_information:
        return responses.user_does_not_exist()

    user_uuid: str = user_information[0][0]  # uuid
    user_email: str = user_information[0][1]  # email
    user_password: str = user_information[0][2]  # password

    if check_password_hash(user_password, password):
        token: str = jwt.encode(
            {
                "uuid": user_uuid,
                "email": user_email,
                "exp": datetime.utcnow() + timedelta(minutes=30),
            },
            app.config["SECRET_KEY"],
        )

        return responses.auth_token(token)

    return responses.could_not_verify()


@app.route("/me", methods=["GET"])
@token_required
def me(unique_id: str, _token: str) -> Response:
    """User's information endpoint."""
    with DatabaseProvider.query(QUERIES.SELECT_USER_DATA_BY_UUID, (unique_id,)) as response:
        if response.message is not Message.OK:
            return responses.internal_database_error(response.message)

        user_information: list = response.data

    if not user_information:
        return responses.user_does_not_exist()

    email: str = user_information[0][0]
    wallet_usd: float = user_information[0][1]
    wallet_btc: float = user_information[0][2]

    return responses.me(unique_id, email, wallet_usd, wallet_btc)


@app.route("/logout", methods=["POST"])
@token_required
def logout(_unique_id: str, token: str) -> Response:
    """Logout endpoint."""
    if is_token_revoked(token):
        return responses.token_already_revoked()

    message: Message = revoke_token(token)
    if message is not Message.OK:
        return responses.internal_database_error(message)

    return responses.successfully_logged_out()


@app.route("/refresh", methods=["POST"])
@token_required
def refresh(unique_id: str, token: str) -> Response:
    """Token refresh endpoint."""
    with DatabaseProvider.query(QUERIES.SELECT_USER_EMAIL_BY_UUID, (unique_id,)) as response:
        if response.message is not Message.OK:
            return responses.internal_database_error(response.message)

        user_information: list[tuple[str]] = response.data

    if not user_information:
        return responses.user_does_not_exist()

    user_email: str = user_information[0][0]

    new_token: str = jwt.encode(
        {
            "uuid": unique_id,
            "email": user_email,
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        app.config["SECRET_KEY"],
    )

    revoke_result: Message = revoke_token(token)
    if revoke_result is not Message.OK:
        return responses.internal_database_error(response.message)

    return responses.auth_token(new_token)


@app.route("/chart")
def chart() -> str:
    """Chart data retrieval endpoint."""
    return "chart"


@app.route("/future_value")
def future_value() -> str:
    """Model data estimation endpoint."""
    return "future_value"


@app.route("/change_password")
def change_password() -> str:
    """User's password change endpoint."""
    return "change_password"


@app.route("/")
def hello_world() -> str:
    """Root endpoint."""
    return "<p>Hello, World!</p>"
