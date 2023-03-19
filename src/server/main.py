from flask import Flask

app = Flask(__name__)


@app.route("/me")
def me() -> str:
    """User's information endpoint."""
    return "me"


@app.route("/login")
def login() -> str:
    """Login endpoint."""
    return "login"


@app.route("/logout")
def logout() -> str:
    """Logout endpoint."""
    return "logout"


@app.route("/register")
def register() -> str:
    """Registration endpoint."""
    return "register"


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
