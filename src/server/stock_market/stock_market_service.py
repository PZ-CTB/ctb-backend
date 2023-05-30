from typing import Optional

from flask import Response

from .. import QUERIES, Responses
from ..database import DatabaseProvider


class StockMarketService:
    """Stock Market Service class."""

    @staticmethod
    def chart(from_param: str, to_param: str, aggregate_param: int) -> Response:
        """Chart data retrieval endpoint handler."""
        filtered_list: list = []

        with DatabaseProvider.handler() as handler:
            if aggregate_param == 1:
                handler().execute(QUERIES.SELECT_CHART, [from_param, to_param])
                data = handler().fetchall()
                filtered_list = [
                    {"date": date.strftime("%Y-%m-%d"), "avg": avg} for date, avg in data
                ]

            else:
                handler().execute(
                    QUERIES.SELECT_CHART_AGGREGATED,
                    (
                        from_param,
                        aggregate_param,
                        from_param,
                        to_param,
                    ),
                )
                data = handler().fetchall()
                filtered_list = [
                    {"date": date.strftime("%Y-%m-%d"), "avg": avg, "low": low, "high": high}
                    for period, date, avg, low, high in data
                ]

        if not handler.success:
            return Responses.internal_database_error(handler.message)

        return Responses.chart(filtered_list)

    @staticmethod
    def price() -> Response:
        """BTC price endpoint service."""
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_LATEST_STOCK_PRICE)
            price: Optional[tuple[str]] = handler().fetchone()

        if not handler.success or price is None:
            print(f"ERROR: cannot retrieve current BTC price from database: {price=}")
            return Responses.internal_database_error(handler.message)

        try:
            price_float: float = float(price[0])
        except Exception:
            print(f"ERROR: cannot convert price '{price[0]}' to float")
            return Responses.internal_database_error(handler.message)
        else:
            return Responses.price(price_float)

    @staticmethod
    def future_value(days: int) -> Response:
        """Future_value prediction endpoint service.

        Args:
            days (int): number of future days' value to return

        Returns:
            Response: future values from database if successful, return error otherwise
        """
        if days > 7:
            days = 7
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_FUTURE_VALUE, (days,))
            future_values: list[tuple[float]] = handler().fetchall()

        if not handler.success or len(future_values) is 0:
            print(f"ERROR: cannot retrieve future values from database: {future_values=}")
            return Responses.internal_database_error(handler.message)
        else:
            return Responses.future_value(future_values)
