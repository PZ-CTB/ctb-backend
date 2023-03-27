import uuid
from datetime import datetime, timedelta
from functools import wraps
from typing import Any, Callable
from uuid import UUID

import jwt
from flask import Flask, Response, make_response, request
from flask_cors import CORS
from werkzeug.security import check_password_hash, generate_password_hash

from . import QUERIES
from .database import DatabaseProvider, Message

DatabaseProvider.initialize()

app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "https://ctb-agh.netlify.app"])
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
            return make_response(
                {"message": "Token is missing"},
                401,
                {"WWW-Authenticate": 'Basic realm ="Token is missing!"'},
            )

        # If the token is revoked return message and exit function
        if is_token_revoked(token):
            return make_response(
                {"message": "Token is revoked"},
                401,
                {"WWW-Authenticate": 'Basic realm ="Token is revoked!"'},
            )

        # Decode the token and retrieve the information contained in it
        try:
            data: dict[str, Any] = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.InvalidTokenError as e:
            return make_response(
                {"message": f"Token is invalid: {e}"},
                401,
                {"WWW-Authenticate": 'Basic realm ="Token is invalid!"'},
            )

        user_uuid: str = data["uuid"]

        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_UUID, (user_uuid,))
            response = handler().fetchall()
        if not handler.success:
            return make_response({"message": f"Internal error: {handler.message}"}, 500)
        user_exists: bool = response != []

        if not user_exists:
            return make_response(
                {"message": "User does not exist"},
                401,
                {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
            )

        # Returns the current logged-in users context to the routes
        return fun(user_uuid, *args, **kwargs)

    return decorated


def revoke_token(token: str) -> Message:
    """Revoking activated token."""
    decoded_token: dict[str, Any] = jwt.decode(
        token, app.config["SECRET_KEY"], algorithms=["HS256"]
    )
    expiry: datetime = datetime.fromtimestamp(decoded_token["exp"])

    with DatabaseProvider.handler() as handler:
        handler().execute(QUERIES.INSERT_REVOKED_TOKEN, (token, expiry))
    return handler.message


def is_token_revoked(token: str) -> bool:
    """Check if token is revoked."""
    with DatabaseProvider.handler() as handler:
        handler().execute(QUERIES.SELECT_REVOKED_TOKEN, (token, datetime.utcnow()))
        is_revoked: bool = handler().fetchall() != []
    if not handler.success:
        return True
    return is_revoked


@app.route("/register", methods=["POST"])
def register() -> Response:
    """Registration endpoint."""
    new_user: dict[str, str] = request.get_json()

    unique_id: UUID = uuid.uuid4()
    email: str = new_user.get("email", "")
    password: str = new_user.get("password", "")

    if not email or not password:
        return make_response({"message": "Invalid Json format"}, 202)

    with DatabaseProvider.handler() as handler:
        handler().execute(QUERIES.SELECT_USER_EMAIL, (email,))
        user_exists: bool = handler().fetchall() != []

    if not handler.success:
        return make_response({"message": f"Internal error: {handler.message}"}, 501)

    if user_exists:
        return make_response(
            {"message": "User already exists. Please Log in."},
            202,
            {"WWW-Authenticate": "User already exists. Please Log in."},
        )

    with DatabaseProvider.handler() as handler:
        handler().execute(
            QUERIES.INSERT_USER, (str(unique_id), email, generate_password_hash(password))
        )
    if not handler.success:
        print(f"ERROR: server.register(): {handler.message}")
        return make_response({"message": f"Internal error: {handler.message}"}, 501)

    return make_response({"message": "Successfully registered"}, 201)


@app.route("/login", methods=["POST"])
def login() -> Response:
    """Login endpoint."""
    auth: dict[str, Any] = request.get_json()

    email: str = auth.get("email", "")
    password: str = auth.get("password", "")

    if not email or not password:
        return make_response({"message": "Invalid Json format"}, 202)

    with DatabaseProvider.handler() as handler:
        handler().execute(QUERIES.SELECT_USER_LOGIN_DATA_BY_EMAIL, (email,))
        user_information: list[tuple[str, str, str]] = handler().fetchall()

    if not handler.success:
        return make_response({"message": f"Internal error: {handler.message}"}, 501)

    if not user_information:
        return make_response(
            {"message": "User does not exist"},
            401,
            {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
        )

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

        return make_response({"auth_token": token}, 201)

    return make_response(
        {"message": "Could not verify"},
        403,
        {"WWW-Authenticate": 'Basic realm ="Wrong password"'},
    )


@app.route("/me", methods=["GET"])
@token_required
def me(unique_id: str) -> Response:
    """User's information endpoint."""
    with DatabaseProvider.handler() as handler:
        handler().execute(QUERIES.SELECT_USER_DATA_BY_UUID, (unique_id,))
        user_information: list = handler().fetchall()
        print(f"{user_information=}")
    print(f"{user_information=}")

    if not handler.success:
        return make_response({"message": f"Internal error: {handler.message}"}, 501)

    if not user_information:
        return make_response(
            {"message": "User does not exist"},
            401,
            {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
        )

    email: str = user_information[0][0]
    wallet_usd: float = user_information[0][1]
    wallet_btc: float = user_information[0][2]

    return make_response(
        {"uuid": unique_id, "email": email, "wallet_usd": wallet_usd, "wallet_btc": wallet_btc},
        200,
    )


@app.route("/logout", methods=["POST"])
@token_required
def logout(_unique_id: str) -> Response:
    """Logout endpoint."""
    token: str = request.headers["x-access-token"]

    if not token:
        return make_response(
            {"message": "Token not delivered"},
            401,
            {"WWW-Authenticate": 'Basic realm ="Token not delivered!"'},
        )

    if is_token_revoked(token):
        return make_response(
            {"message": "Token already revoked"},
            401,
            {"WWW-Authenticate": 'Basic realm ="Token already revoked!"'},
        )

    if revoke_token(token) is not Message.OK:
        return make_response({"message": "Internal error"}, 501)

    return make_response({"message": "User is successfully logged out"}, 201)


@app.route("/refresh", methods=["POST"])
@token_required
def refresh(unique_id: str) -> Response:
    """Token refresh endpoint."""
    with DatabaseProvider.handler() as handler:
        handler().execute(QUERIES.SELECT_USER_EMAIL_BY_UUID, (unique_id,))
        user_information: list[tuple[str]] = handler().fetchall()

    if not handler.success:
        return make_response({"message": f"Internal error: {handler.message}"}, 500)

    if not user_information:
        return make_response(
            {"message": "User does not exist"},
            401,
            {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
        )

    user_email: str = user_information[0][0]

    new_token: str = jwt.encode(
        {
            "uuid": unique_id,
            "email": user_email,
            "exp": datetime.utcnow() + timedelta(minutes=30),
        },
        app.config["SECRET_KEY"],
    )

    # Token exists -> checked by decorator
    token: str = request.headers["x-access-token"]
    revoke_result: Message = revoke_token(token)
    if revoke_result is not Message.OK:
        return make_response({"message": f"Internal error: {revoke_result}"}, 501)

    return make_response({"auth_token": new_token}, 201)


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
