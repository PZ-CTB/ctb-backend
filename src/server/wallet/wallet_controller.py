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

    @staticmethod
    @blueprint.route("/withdraw", methods=["POST"])
    @SchemaValidator.validate("withdraw")
    @TokenService.token_required
    def withdraw(uuid: str, _token: str) -> Response:
        """Withdraw endpoint."""
        body: dict[str, int] = request.get_json()

        amount: int = body.get("amount", 0)

        return WalletService.withdraw(uuid, amount)

    @staticmethod
    @blueprint.route("/buy", methods=["POST"])
    @SchemaValidator.validate("buy")
    @TokenService.token_required
    def buy(uuid: str, _token: str) -> Response:
        """Buying endpoint."""
        body: dict[str, int] = request.get_json()

        amount: int = body.get("amount", 0)

        return WalletService.buy(uuid, amount)

    @staticmethod
    @blueprint.route("/sell", methods=["POST"])
    @SchemaValidator.validate("sell")
    @TokenService.token_required
    def sell(uuid: str, _token: str) -> Response:
        """Selling endpoint."""
        body: dict[str, int] = request.get_json()

        amount: int = body.get("amount", 0)

        return WalletService.sell(uuid, amount)
