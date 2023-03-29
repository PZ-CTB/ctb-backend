from typing import Any

from flask import Blueprint, Response, request

from . import AuthService, TokenService


class AuthController:
    """Authentication controller class.

    Exposes multiple endpoints for authentication related purposes.
    """

    blueprint: Blueprint = Blueprint("auth", __name__, url_prefix="/auth")

    @staticmethod
    @blueprint.route("/register", methods=["POST"])
    def register() -> Response:
        """Registration endpoint."""
        new_user: dict[str, str] = request.get_json()

        email: str = new_user.get("email", "")
        password: str = new_user.get("password", "")

        return AuthService.register(email, password)

    @staticmethod
    @blueprint.route("/login", methods=["POST"])
    def login() -> Response:
        """Login endpoint."""
        auth: dict[str, Any] = request.get_json()

        email: str = auth.get("email", "")
        password: str = auth.get("password", "")

        return AuthService.login(email, password)

    @staticmethod
    @blueprint.route("/me", methods=["GET"])
    @TokenService.token_required
    def me(uuid: str, _token: str) -> Response:
        """User's information endpoint."""
        return AuthService.me(uuid)

    @staticmethod
    @blueprint.route("/logout", methods=["POST"])
    @TokenService.token_required
    def logout(_uuid: str, token: str) -> Response:
        """Logout endpoint."""
        return AuthService.logout(token)

    @staticmethod
    @blueprint.route("/refresh", methods=["POST"])
    @TokenService.token_required
    def refresh(uuid: str, token: str) -> Response:
        """Token refresh endpoint."""
        return TokenService.refresh(uuid, token)

    @staticmethod
    @blueprint.route("/change_password")
    def change_password() -> str:
        """User's password change endpoint."""
        return "change_password"
