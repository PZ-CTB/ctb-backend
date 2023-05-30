from flask import Blueprint, Response, request

from .. import Responses, SchemaValidator
from . import StockMarketService


class StockMarketController:
    """Stock Market Controller class."""

    blueprint = Blueprint("stock", __name__, url_prefix="/stock")

    @staticmethod
    @blueprint.route("/chart")
    def chart() -> Response:
        """Chart data retrieval endpoint."""
        args = request.args
        from_param: str = args.get("from", "")
        to_param: str = args.get("to", "")
        aggregate_param: int = int(args.get("aggregate", 1))

        if from_param == "" or to_param == "":
            return Responses.chart_missing_parameters_error()

        return StockMarketService.chart(from_param, to_param, aggregate_param)

    @staticmethod
    @blueprint.route("/price", methods=["GET"])
    def price() -> Response:
        """BTC price retrieval endpoint."""
        return StockMarketService.price()

    @staticmethod
    @blueprint.route("/future_value", methods=["POST"])
    @SchemaValidator.validate("future_value")
    def future_value() -> Response:
        """Model data estimation endpoint."""
        body: dict[str, int] = request.get_json()

        days: int = body.get("days", 0)

        return StockMarketService.future_value(days)
