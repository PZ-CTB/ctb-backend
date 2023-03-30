from flask import Blueprint


class StockMarketController:
    """Stock Market Controller class."""

    blueprint = Blueprint("stock", __name__, url_prefix="/stock")

    @staticmethod
    @blueprint.route("/chart")
    def chart() -> str:
        """Chart data retrieval endpoint."""
        return "chart"

    @staticmethod
    @blueprint.route("/future_value")
    def future_value() -> str:
        """Model data estimation endpoint."""
        return "future_value"
