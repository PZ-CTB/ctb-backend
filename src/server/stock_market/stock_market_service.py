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
                filtered_list = [{"date": date.strftime("%Y-%m-%d"), "avg": avg} for date, avg in data]

            else:
                # aggregate_seconds: int = int(aggregate_param) * 3600 * 24
                handler().execute(
                    QUERIES.SELECT_CHART_AGGREGATED,
                    (from_param, aggregate_param, from_param, to_param,)
                )
                data = handler().fetchall()
                filtered_list = [
                    {"date": date.strftime("%Y-%m-%d"), "avg": avg, "low": low, "high": high}
                    for period, date, avg, low, high in data
                ]

        if not handler.success:
            return Responses.internal_database_error(handler.message)

        return Responses.chart(filtered_list)
