import json
import uuid
from datetime import datetime, timedelta
from functools import wraps
from sqlite3 import Connection, Cursor
from sqlite3 import Error as SqlError
from typing import Any, Callable
from uuid import UUID

import jwt
from flask import Flask, Response, make_response, request
from werkzeug.security import check_password_hash, generate_password_hash

from .database_provider import getDatabaseConnection

data = dict()
with open("./res/datasets/dummy_data.json", "r") as file:
    data = json.loads(file.read())

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

        try:
            connection: Connection = getDatabaseConnection()
            sql: str = "SELECT uuid, email FROM users WHERE uuid=?"
            cursor: Cursor = connection.cursor()
            cursor.execute(sql, (data["uuid"],))
            user_information: list[tuple[str, str]] = cursor.fetchall()
            connection.close()
        except SqlError as e:
            return make_response({"message": f"Database connection error: {e}"}, 500)

        if not user_information:
            return make_response(
                {"message": "User does not exist"},
                401,
                {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
            )

        # Retrieve user uuid
        unique_id: str = user_information[0][0]

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
    email: str = new_user.get("email", "")
    password: str = new_user.get("password", "")

    if not email or not password:
        return make_response({"message": "Invalid Json format"}, 202)

    try:
        connection: Connection = getDatabaseConnection()
        sql: str = "SELECT * FROM users WHERE email=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (email,))
        user_information: list[tuple] = cursor.fetchall()
        connection.close()
    except SqlError as e:
        return make_response({"message": f"Database connection error: {e}"}, 501)

    if user_information:
        return make_response(
            {"message": "User already exists. Please Log in."},
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
        return make_response({"message": f"Database connection error: {e}"}, 501)

    return make_response({"message": "Successfully registered"}, 201)


@app.route("/login", methods=["POST"])
def login() -> Response:
    """Login endpoint."""
    auth: dict[str, Any] = request.json

    email: str = auth.get("email", "")
    password: str = auth.get("password", "")

    if not email or not password:
        return make_response({"message": "Invalid Json format"}, 202)

    try:
        connection: Connection = getDatabaseConnection()
        sql: str = "SELECT uuid, email, password_hash FROM users WHERE email=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (email,))
        user_information: list[tuple[str, str, str]] = cursor.fetchall()
        connection.close()
    except SqlError as e:
        return make_response({"message": f"Database connection error: {e}"}, 501)

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

        return make_response({"AUTH-TOKEN": token}, 201)

    return make_response(
        {"message": "Could not verify"},
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
        return make_response({"message": f"Database connection error: {e}"}, 501)

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

    try:
        revoke_token(token)
    except SqlError as e:
        return make_response({"message": f"Database connection error: {e}"}, 501)

    return make_response({"message": "User is successfully logged out"}, 201)


@app.route("/refresh", methods=["POST"])
@token_required
def refresh(unique_id: str) -> Response:
    """Token refresh endpoint."""
    try:
        connection: Connection = getDatabaseConnection()
        sql: str = "SELECT email FROM users WHERE uuid=?"
        cursor: Cursor = connection.cursor()
        cursor.execute(sql, (unique_id,))
        user_information: list[tuple[str, str]] = cursor.fetchall()
        connection.close()
    except SqlError as e:
        return make_response({"message": f"Database connection error: {e}"}, 500)

    user_email: str = ""

    if not user_information:
        return make_response(
            {"message": "User does not exist"},
            401,
            {"WWW-Authenticate": 'Basic realm ="User does not exist!"'},
        )

    user_email = user_information[0][0]

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
    try:
        revoke_token(token)
    except SqlError as e:
        return make_response({"message": f"Database connection error: {e}"}, 501)

    return make_response({"AUTH-TOKEN": new_token}, 201)


@app.route("/chart")
def chart() -> Response:
    """Chart data retrieval endpoint."""
    args = request.args
    aggregate_param = int(args.get("aggregate", 1))
    aggregate_seconds = int(aggregate_param) * 3600 * 24
    from_param = args.get("from")
    to_param = args.get("to")
    if from_param == None or to_param == None:
        return Response("Please provide both from and to parameters!", 400)

    db = getDatabaseConnection()
    cur = db.cursor()
    filtered_list = []

    if aggregate_param == 1:
        cur.execute(
            """ SELECT date, value FROM exchange_rate_history
                        WHERE date BETWEEN ? and ?
                        ORDER BY date""",
            [from_param, to_param],
        )
        filtered_list = [{"date": date, "avg": avg} for date, avg in cur]
    else:
        cur.execute(
            """ SELECT MIN(date), AVG(value), MIN(value), MAX(value) FROM exchange_rate_history
                        WHERE date BETWEEN ? and ?
                        GROUP BY ROUND((STRFTIME("%s", ?) - timestamp)/(?) - 0.5)
                        ORDER BY MIN(date)""",
            [from_param, to_param, to_param, aggregate_seconds],
        )

        filtered_list = [
            {"date": date, "avg": avg, "low": low, "high": high} for date, avg, low, high in cur
        ]

    return Response(json.dumps(filtered_list).encode("utf-8"), 200)


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
