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
                filtered_list = [{"date": date, "avg": avg} for date, avg in data]

            else:
                aggregate_seconds: int = int(aggregate_param) * 3600 * 24
                handler().execute(
                    QUERIES.SELECT_CHART_AGGREGATED,
                    [from_param, to_param, to_param, aggregate_seconds],
                )
                data = handler().fetchall()
                filtered_list = [
                    {"date": date, "avg": avg, "low": low, "high": high}
                    for date, avg, low, high in data
                ]

        if not handler.success:
            return Responses.internal_database_error(handler.message)

        return Responses.chart(filtered_list)
