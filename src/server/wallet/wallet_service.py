from typing import Union

from flask import Response

from .. import QUERIES, Responses
from ..constants import CONSTANTS
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
            user_data: list[tuple[str, str, str]] = handler().fetchall()
        if not handler.success:
            print(f"ERROR: server.wallet.wallet_service.balance: {handler.message}")
            return Responses.internal_database_error(handler.message)

        if user_data:
            _, usd_balance, btc_balance = user_data[0]
            return Responses.balance(float(usd_balance), float(btc_balance))
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
        if amount > CONSTANTS.MAXIMUM_ALLOWED_OPERATION_AMOUNT:
            return Responses.maximum_possible_value_exceeded()
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
        if amount > CONSTANTS.MAXIMUM_ALLOWED_OPERATION_AMOUNT:
            return Responses.maximum_possible_value_exceeded()
        # Check if user has enough money to withdraw
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_DATA_BY_UUID, (uuid,))
            user_data: tuple[str, str, str] = handler().fetchone()
            if not user_data:
                return Responses.internal_server_error()
            if float(user_data[1]) < amount:
                return Responses.not_enough_money_to_withdraw()
            else:
                handler().execute(QUERIES.WALLET_WITHDRAW, (amount, uuid))
        if not handler.success:
            print(f"ERROR: server.wallet.wallet_service.withdraw: {handler.message}")
            return Responses.internal_database_error(handler.message)

        return Responses.successfully_withdrawn()

    @staticmethod
    def buy(uuid: str, amount: float) -> Response:
        """Buying method.

        Args:
            uuid (str): user's uuid,
            amount (float): amount of BTC to buy.

        Returns:
            Response: successfully_bought if transaction succeed, return error otherwise.

        """
        if amount > CONSTANTS.MAXIMUM_ALLOWED_OPERATION_AMOUNT:
            return Responses.maximum_possible_value_exceeded()
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_DATA_BY_UUID, (uuid,))
            user_data: tuple[str, str, str] = handler().fetchone()
            if user_data:
                handler().execute(QUERIES.SELECT_LATEST_STOCK_PRICE)
                price: tuple[str] = handler().fetchone()
                if price:
                    total_price = float(price[0]) * amount
                    # Check if user has enough money to perform transaction
                    if float(user_data[1]) >= total_price:
                        handler().execute(QUERIES.WALLET_BUY, (total_price, amount, uuid))
                    else:
                        return Responses.not_enough_money_to_make_a_purchase()
                else:
                    return Responses.internal_server_error()
            else:
                return Responses.internal_server_error()
        if not handler.success:
            print(f"ERROR: server.wallet.wallet_service.buy: {handler.message}")
            return Responses.internal_database_error(handler.message)

        return Responses.successfully_bought()

    @staticmethod
    def sell(uuid: str, amount: float) -> Response:
        """Selling method.

        Args:
            uuid (str): user's uuid,
            amount (float): amount of BTC to sell.

        Returns:
            Response: successfully_sold if transaction succeed, return error otherwise.

        """
        if amount > CONSTANTS.MAXIMUM_ALLOWED_OPERATION_AMOUNT:
            return Responses.maximum_possible_value_exceeded()
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_USER_DATA_BY_UUID, (uuid,))
            user_data: tuple[str, str, str] = handler().fetchone()
            if user_data:
                # Check if user has enough BTC to perform transaction
                if float(user_data[2]) >= amount:
                    handler().execute(QUERIES.SELECT_LATEST_STOCK_PRICE)
                    price: tuple[str] = handler().fetchone()
                    if price:
                        total_price = float(price[0]) * amount
                        handler().execute(QUERIES.WALLET_SELL, (total_price, amount, uuid))
                    else:
                        return Responses.internal_server_error()
                else:
                    return Responses.not_enough_BTC_to_make_a_sale()
            else:
                return Responses.internal_server_error()
        if not handler.success:
            print(f"ERROR: server.wallet.wallet_service.sell: {handler.message}")
            return Responses.internal_database_error(handler.message)

        return Responses.successfully_sold()

    @staticmethod
    def history(uuid: str) -> Response:
        """Get user's transaction history.

        Args:
            uuid (str): user's uuid.

        Returns:
            Response: List of transactions if operation succeeded, appropriate error otherwise.

        """
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.WALLET_TRANSACTION_HISTORY, (uuid,))
            transaction_history: list[tuple[str, str, str, str, str, str]] = handler().fetchall()
        if not handler.success:
            print(f"ERROR: server.wallet.wallet_service.history: {handler.message}")
            return Responses.internal_database_error(handler.message)

        transactions: list[dict[str, Union[str, float]]] = []
        for transaction in transaction_history:
            transactions.append(
                (
                    {
                        "timestamp": transaction[0],
                        "type": transaction[1],
                        "amount_usd": float(transaction[2]),
                        "amount_btc": float(transaction[3]),
                        "total_usd_after_transaction": float(transaction[4]),
                        "total_btc_after_transaction": float(transaction[5]),
                    }
                )
            )
        return Responses.transaction_history(transactions)
