from flask import Blueprint, Flask
from flask_cors import CORS
from flask_swagger_ui import get_swaggerui_blueprint

from . import SchemaValidator
from .auth import AuthController
from .constants import QUERIES
from .database import DatabaseProvider
from .stock_market import StockMarketController
from .wallet import WalletController


class Server:
    """Main application start point."""

    def __init__(self) -> None:
        """Initialize server application along with its endpoints and cors."""
        DatabaseProvider.initialize()
        SchemaValidator.initialize()

        self.name: str = __name__
        self.app: Flask = self._create_app()
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.cors: CORS = CORS(
            self.app, origins=["http://localhost:3000", "https://ctb-agh.netlify.app"]
        )
        self._setup_endpoints()

    def _create_app(self) -> Flask:
        """Create Flask server."""
        return Flask(self.name)

    def _setup_endpoints(self) -> None:
        """Create endpoints on the Flask server."""
        self.app.add_url_rule("/", view_func=hello_world_endpoint)
        self.swagger: Blueprint = get_swaggerui_blueprint("/api/v1/swagger", "/static/openapi.yaml")

        self.api: Blueprint = Blueprint("api", self.name, url_prefix="/api")
        self.v1: Blueprint = Blueprint("v1", self.name, url_prefix="/v1")
        self.v1.register_blueprint(self.swagger, url_prefix="/swagger")
        self.v1.register_blueprint(AuthController.blueprint)
        self.v1.register_blueprint(StockMarketController.blueprint)
        self.v1.register_blueprint(WalletController.blueprint)
        self.api.register_blueprint(self.v1)
        self.app.register_blueprint(self.api)


def hello_world_endpoint() -> str:
    """Root endpoint."""
    try:
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.HELLO_WORLD_QUERY)
            (db_hello_world,) = handler().fetchone()  # type: ignore
    except:
        # no matter why, show something else than it would show if it worked correctly
        db_hello_world = "Goodbye, World!"
    return f"<p>Hello, World!</p><p>{db_hello_world}</p>"


def create_app() -> Flask:
    """Server launch."""
    server = Server()
    return server.app
