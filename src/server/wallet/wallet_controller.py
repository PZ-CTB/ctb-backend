from flask import Blueprint, Response, request

from .. import SchemaValidator
from ..auth import TokenService
from . import WalletService


class WalletController:
    """Wallet Controller class.

    Allows authorized users to perform operations on their wallet.
    """

    blueprint: Blueprint = Blueprint("wallet", __name__, url_prefix="/wallet")

    @staticmethod
    @blueprint.route("/balance", methods=["GET"])
    @TokenService.token_required
    def balance(uuid: str, _token: str) -> Response:
        """Balance endpoint."""
        return WalletService.balance(uuid)

    @staticmethod
    @blueprint.route("/deposit", methods=["POST"])
    @SchemaValidator.validate("deposit")
    @TokenService.token_required
    def deposit(uuid: str, _token: str) -> Response:
        """Deposit endpoint."""
        body: dict[str, int] = request.get_json()

        amount: int = body.get("amount", 0)

        return WalletService.deposit(uuid, amount)