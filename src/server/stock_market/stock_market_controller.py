from flask import Blueprint, Response, request

from .. import Responses
from . import StockMarketService


class StockMarketController:
    """Stock Market Controller class."""

    blueprint = Blueprint("stock", __name__, url_prefix="/stock")

    @staticmethod
    @blueprint.route("/chart")
    def chart() -> Response:
        """Chart data retrieval endpoint."""
        args = request.args
        from_param: str | None = args.get("from")
        to_param: str | None = args.get("to")
        aggregate_param: int = int(args.get("aggregate", 1))

        if from_param is None or to_param is None:
            return Responses.chart_missing_parameters_error()

        return StockMarketService.chart(from_param, to_param, aggregate_param)

    @staticmethod
    @blueprint.route("/future_value")
    def future_value() -> str:
        """Model data estimation endpoint."""
        return "future_value"
