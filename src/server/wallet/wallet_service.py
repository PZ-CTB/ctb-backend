from flask import Response

from .. import QUERIES, Responses
from ..database import DatabaseProvider


class WalletService:
    """Wallet Service class."""

    @staticmethod
    def balance(uuid: str) -> Response:
        """Get user's account balance.

        Args:
            uuid (str): user's UUID.

        Returns:
            Response: Account balance if operation succeeded, appropriate error otherwise.

        """
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_DATA_BY_UUID, (uuid,))
            user_data: list[tuple[str, float, float]] = handler().fetchall()

        if not handler.success:
            print(f"ERROR: server.wallet.wallet_service.balance: {handler.message}")
            return Responses.internal_database_error(handler.message)

        if user_data:
            _, usd_balance, btc_balance = user_data[0]
            return Responses.balance(usd_balance, btc_balance)
        else:
            return Responses.unauthorized_error()

    @staticmethod
    def deposit(uuid: str, amount: float) -> Response:
        """Deposit method.

        Args:
            uuid (str): user`s uuid,
            amount (float): amount to deposit.

        Returns:
            Response: successfully_deposited if deposit succeed, appropriate error otherwise.

        """
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.WALLET_DEPOSIT, (amount, uuid))
        if not handler.success:
            print(f"ERROR: server.wallet.wallet_service.deposit: {handler.message}")
            return Responses.internal_database_error(handler.message)

        return Responses.successfully_deposited()

    @staticmethod
    def withdraw(uuid: str, amount: float) -> Response:
        """Withdraw method.

        Args:
            uuid (str): user`s uuid,
            amount (float): amount to withdraw.

        Returns:
            Response: successfully_withdrawn if withdrawal succeeded, appropriate error otherwise.

        """
        # Check if user has enough money to withdraw
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_DATA_BY_UUID, (uuid,))
            user_data = handler().fetchone()
            if not user_data:
                return Responses.internal_server_error()
            if user_data[0][1] < amount:
                return Responses.not_enough_money_to_withdraw()
            else:
                handler().execute(QUERIES.WALLET_WITHDRAW, (amount, uuid))
        if not handler.success:
            print(f"ERROR: server.wallet.wallet_service.withdraw: {handler.message}")
            return Responses.internal_database_error(handler.message)

        return Responses.successfully_withdrawn()
