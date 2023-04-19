from flask import Blueprint, Response, request

from ..auth import TokenService
from .. import SchemaValidator
from . import WalletService


class WalletController:
    """Wallet Controller class.

    Allows to user to perform operations on their wallet."""

    blueprint = Blueprint("wallet", __name__, url_prefix="/wallet")

    @staticmethod
    @blueprint.route("/deposit")
    @SchemaValidator.validate(SchemaValidator.deposit_schema)
    @TokenService.token_required
    def deposit(uuid: str, _token: str) -> Response:
        """Deposit endpoint."""
        body: dict[str, int] = request.get_json()

        amount: int = body.get("amount", 0)

        return WalletService.deposit(uuid, amount)
