import json
import uuid
from datetime import datetime, timedelta
from functools import wraps
from sqlite3 import Connection, Cursor
from sqlite3 import Error as SqlError
from typing import Any, Callable
from uuid import UUID

import jwt  # type: ignore
from flask import Flask, Response, make_response, request  # type: ignore
from werkzeug.security import (  # type: ignore
    check_password_hash,
    generate_password_hash,
)

from .database_provider import getDatabaseConnection

app = Flask(__name__)
# Generetion method -> uuid.uuid4().hex
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
                json.dumps({"message": "Token is missing"}),
                401,
                {"WWW-Authenticate": 'Basic realm ="Token is missing!"'},
            )

        # If the token is revoked return message and exit function
        if is_token_revoked(token):
            return make_response(
                json.dumps({"message": "Token is revoked"}),
                401,
                {"WWW-Authenticate": 'Basic realm ="Token is revoked!"'},
            )

        # Decode the token and retrieve the information contained in it
        try:
            data: dict[str, Any] = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
        except jwt.InvalidTokenError as e:
            return make_response(
                json.dumps({"message": f"Token is invalid: {e}"}),
                401,
                {"WWW-Authenticate": 'Basic realm ="Token is invalid!"'},
            )

        try:
            connection: Connection = getDatabaseConnection()
            sql: str = "SELECT uuid, email FROM users WHERE uuid=?"
            cursor: Cursor = connection.cursor()
            cursor.execute(sql, (data["uuid"],))
            user_information: list[tuple[str, str]] = cursor.fetchall()
            connection.close()
        except SqlError as e:
            return make_response(json.dumps({"message": f"Database connection error: {e}"}), 500)

        unique_id: str = ""

        if not user_information:
            return make_response(
                json.dumps({"message": "User does not exist"}),
                401,
                {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
            )

        # Retrieve user uuid
        unique_id = user_information[0][0]

        # Returns the current logged-in users context to the routes
        return fun(unique_id, *args, **kwargs)

    return decorated


def revoke_token(token: str) -> None:
    """Revoking activated token."""
    decoded_token: dict[str, Any] = jwt.decode(
        token, app.config["SECRET_KEY"], algorithms=["HS256"]
    )
    expiry: datetime = datetime.fromtimestamp(decoded_token["exp"])

    # Saving revoked token into the database
    try:
        connection: Connection = getDatabaseConnection()
        connection.execute(
            "INSERT INTO revoked_tokens (token, expiry) VALUES (?, ?)",
            (
                token,
                expiry,
            ),
        )
        connection.commit()
        connection.close()
    except SqlError as e:
        raise SqlError(f"Database connection error: {str(e)}") from e

    return None


def is_token_revoked(token: str) -> bool:
    """Check if token is revoked."""
    try:
        connection: Connection = getDatabaseConnection()
        result: Cursor = connection.execute(
            "SELECT token FROM revoked_tokens WHERE token=? AND expiry > ?",
            (
                token,
                datetime.utcnow(),
            ),
        )
        is_revoked: bool = result.fetchone() is not None
        connection.close()
    except SqlError:
        return True

    return is_revoked


@app.route("/register", methods=["POST"])
def register() -> Response:
    """Registration endpoint."""
    new_user: dict[str, str] = request.json

    unique_id: UUID = uuid.uuid4()
    try:
        email: str = new_user["email"]
        password: str = new_user["password"]
        repeated_password: str = new_user["repeatedPassword"]
    except KeyError as e:
        return make_response(json.dumps({"message": f"Invalid Json format: {e}"}), 202)

    if password != repeated_password:
        return make_response(
            json.dumps({"message": "Passwords doesn't match"}),
            202,
            {"WWW-Authenticate": "Passwords doesn't match"},
        )

    try:
        connection: Connection = getDatabaseConnection()
        sql: str = "SELECT * FROM users WHERE email=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (email,))
        user_information: list[tuple] = cursor.fetchall()
        connection.close()
    except SqlError as e:
        return make_response(json.dumps({"message": f"Database connection error: {e}"}), 501)

    if user_information:
        return make_response(
            json.dumps({"message": "User already exists. Please Log in."}),
            202,
            {"WWW-Authenticate": "User already exists. Please Log in."},
        )

    try:
        # Already defined: connection, sql, cursor
        connection = getDatabaseConnection()
        sql = "INSERT INTO users(uuid, email, password_hash) VALUES (?, ?, ?)"
        cursor = connection.cursor()
        cursor.execute(
            sql,
            (
                str(unique_id),
                email,
                generate_password_hash(password),
            ),
        )
        connection.commit()
        connection.close()
    except SqlError as e:
        return make_response(json.dumps({"message": f"Database connection error: {e}"}), 501)

    return make_response(json.dumps({"message": "Successfully registered"}), 201)


@app.route("/login", methods=["POST"])
def login() -> Response:
    """Login endpoint."""
    auth: dict[str, Any] = request.json

    try:
        email: str = auth["email"]
        password: str = auth["password"]
    except KeyError as e:
        return make_response(json.dumps({"message": f"Invalid Json format: {e}"}), 202)

    try:
        connection: Connection = getDatabaseConnection()
        sql: str = "SELECT uuid, email, password_hash FROM users WHERE email=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (email,))
        user_information: list[tuple[str, str, str]] = cursor.fetchall()
        connection.close()
    except SqlError as e:
        return make_response(json.dumps({"message": f"Database connection error: {e}"}), 501)

    if not user_information:
        return make_response(
            json.dumps({"message": "User does not exist"}),
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

        return make_response(json.dumps({"AUTH-TOKEN": token}), 201)

    return make_response(
        json.dumps({"message": "Could not verify"}),
        403,
        {"WWW-Authenticate": 'Basic realm ="Wrong password"'},
    )


@app.route("/me", methods=["GET"])
@token_required
def me(unique_id: str) -> Response:
    """User's information endpoint."""
    try:
        connection: Connection = getDatabaseConnection()
        sql = "SELECT email, wallet_usd, wallet_btc FROM users WHERE uuid=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (unique_id,))
        user_information: list = cursor.fetchall()
        connection.close()
    except SqlError as e:
        return make_response(json.dumps({"message": f"Database connection error: {e}"}), 501)

    if not user_information:
        return make_response(
            json.dumps({"message": "User does not exist"}),
            401,
            {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
        )

    email: str = user_information[0][0]
    wallet_usd: float = user_information[0][1]
    wallet_btc: float = user_information[0][2]

    return make_response(
        json.dumps(
            {"uuid": unique_id, "email": email, "wallet_usd": wallet_usd, "wallet_btc": wallet_btc}
        ),
        200,
    )


@app.route("/logout", methods=["POST"])
@token_required
def logout(_unique_id: str) -> Response:
    """Logout endpoint."""
    token: str = request.headers["x-access-token"]

    if not token:
        return make_response(
            json.dumps({"message": "Token not delivered"}),
            401,
            {"WWW-Authenticate": 'Basic realm ="Token not delivered!"'},
        )

    if is_token_revoked(token):
        return make_response(
            json.dumps({"message": "Token already revoked"}),
            401,
            {"WWW-Authenticate": 'Basic realm ="Token already revoked!"'},
        )

    try:
        revoke_token(token)
    except SqlError as e:
        return make_response(json.dumps({"message": f"Database connection error: {e}"}), 501)

    return make_response(json.dumps({"message": "User is successfully logged out"}), 201)


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
