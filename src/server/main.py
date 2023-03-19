import uuid
from datetime import datetime, timedelta
from functools import wraps
from sqlite3 import Connection, Cursor
from typing import Any
from uuid import UUID

import jwt
from flask import Flask, Response, jsonify, make_response, request
from werkzeug.security import check_password_hash, generate_password_hash

from .database_provider import getDatabaseConnection

app = Flask(__name__)
# Generetion method -> uuid.uuid4().hex
app.config["SECRET_KEY"] = "55cfba6d5bd6405c8e9b7b681f6b8835"

# decorator for verifying the JWT
def token_required(fun) -> Any:
    """Validate received token."""

    @wraps(fun)
    def decorated(*args, **kwargs) -> Any:
        """Validate received token."""
        token: str = None
        # JWT is passed in the request header
        if "x-access-token" in request.headers:
            token = request.headers["x-access-token"]

        # If the token is not passed return message and exit function
        if not token:
            return jsonify({"message": "Token is missing!"}), 401

        # If the token is revoked return message and exit function
        if is_token_revoked(token):
            return jsonify({"message": "Token is revoked!"}), 401

        # Decode the token and retrieve the information contained in it
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])

            try:
                connection: Connection = getDatabaseConnection()
                sql: str = "SELECT uuid, email FROM users WHERE uuid=?"
                cursor: Cursor = connection.cursor()
                cursor.execute(sql, (data["uuid"],))
                user_information: list = cursor.fetchall()
                connection.close()
            except:
                return jsonify({"message": "Database connection error!"}), 500

            unique_id: str = None
            email: str = None

            if user_information:
                # Retrieve user uuid
                unique_id = user_information[0][0]  # uuid
                # Retrieve user email
                email = user_information[0][1]  # email
        except:
            return jsonify({"message": "Token is invalid !"}), 401

        # Returns the current logged-in users context to the routes
        return fun(unique_id, email, *args, **kwargs)

    return decorated


def revoke_token(token) -> Any:
    """Revoking activated token."""
    decoded_token: str = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
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
    except:
        return jsonify({"message": "Database connection error!"}), 500


def is_token_revoked(token) -> Any:
    """Check if token is revoked."""
    try:
        connection: Connection = getDatabaseConnection()
        result = connection.execute(
            "SELECT token FROM revoked_tokens WHERE token=? AND expiry > ?",
            (
                token,
                datetime.utcnow(),
            ),
        )
        is_revoked: bool = result.fetchone() is not None
        connection.close()
    except:
        return jsonify({"message": "Token is invalid !"}), 401

    return is_revoked


@app.route("/register", methods=["POST"])
def register() -> Response:
    """Registration endpoint."""
    new_user: Any = request.json

    unique_id: UUID = uuid.uuid4()
    email: str = new_user["email"]
    password: str = new_user["password"]
    repeated_password: str = new_user["repeatedPassword"]

    if password != repeated_password:
        return make_response(
            "Passwords doesn't match", 202, {"WWW-Authenticate": "Passwords doesn't match"}
        )

    try:
        connection: Connection = getDatabaseConnection()
        sql = "SELECT * FROM users WHERE email=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (email,))
        user_information: list = cursor.fetchall()
        connection.close()
    except:
        return jsonify({"message": "Database connection error!"}), 500

    if user_information:
        return make_response(
            "User already exists. Please Log in.",
            202,
            {"WWW-Authenticate": "User already exists. Please Log in."},
        )

    try:
        connection: Connection = getDatabaseConnection()
        sql = "INSERT INTO users(uuid, email, password_hash) VALUES (?, ?, ?)"
        cursor: Cursor = connection.cursor()
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
    except:
        return jsonify({"message": "Database connection error!"}), 500

    return make_response("Successfully registered.", 201)


@app.route("/login", methods=["POST"])
def login() -> Response:
    """Login endpoint."""
    auth: Any = request.json

    email: str = auth["email"]
    password: str = auth["password"]

    try:
        connection: Connection = getDatabaseConnection()
        sql: str = "SELECT uuid, email, password_hash FROM users WHERE email=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (email,))
        user_information: list = cursor.fetchall()
        connection.close()
    except:
        return jsonify({"message": "Database connection error!"}), 500

    user_uuid: str = None
    user_email: str = None
    user_password: str = None

    if not user_information:
        return make_response(
            "Could not verify", 401, {"WWW-Authenticate": 'Basic realm ="User does not exist!"'}
        )
    else:
        user_uuid = user_information[0][0]  # uuid
        user_email = user_information[0][1]  # email
        user_password = user_information[0][2]  # password

    if check_password_hash(user_password, password):
        token = jwt.encode(
            {
                "uuid": user_uuid,
                "email": user_email,
                "exp": datetime.utcnow() + timedelta(minutes=30),
            },
            app.config["SECRET_KEY"],
        )

        return make_response(jsonify({"token": token}), 201)

    # returns 403 if password is wrong
    return make_response(
        "Could not verify", 403, {"WWW-Authenticate": 'Basic realm ="Wrong Password!"'}
    )


@app.route("/me", methods=["GET"])
@token_required
def me(unique_id, email) -> Response:
    """User's information endpoint."""
    try:
        connection: Connection = getDatabaseConnection()
        sql = "SELECT uuid, email, wallet_usd, wallet_btc FROM users WHERE email=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (email,))
        user_information: list = cursor.fetchall()
        connection.close()
    except:
        return jsonify({"message": "Database connection error!"}), 500

    if user_information:
        uuid: str = user_information[0][0]
        email: str = user_information[0][1]
        walled_usd: float = user_information[0][2]
        wallet_btc: float = user_information[0][3]
    else:
        return make_response(
            "Could not verify", 401, {"WWW-Authenticate": 'Basic realm ="User does not exist!"'}
        )

    prepared_info = {
        "uuid": uuid,
        "email": email,
        "wallet_usd": walled_usd,
        "wallet_btc": wallet_btc,
    }

    return jsonify(prepared_info)


@app.route("/logout", methods=["POST"])
@token_required
def logout(unique_id, email) -> Response:
    """Logout endpoint."""
    token: str = request.headers["x-access-token"]
    if token:
        revoke_token(token)
    else:
        return make_response(
            "Token not delivered", 401, {"WWW-Authenticate": 'Basic realm ="Token not delivered!"'}
        )

    return make_response("Successfully logged out.", 201)


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
