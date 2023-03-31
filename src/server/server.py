from flask import Blueprint, Flask
from flask_cors import CORS
from werkzeug.serving import BaseWSGIServer, make_server

from .auth import AuthController
from .database import DatabaseProvider
from .stock_market import StockMarketController


class Server:
    """Main application start point."""

    def __init__(self) -> None:
        """Initialize server application along with its endpoints and cors."""
        DatabaseProvider.initialize()

        self.name: str = __name__
        self.app: Flask = self._create_app()
        self.server: BaseWSGIServer = make_server("127.0.0.1", 5000, self.app)
        self.ctx = self.app.app_context()
        self.ctx.push()

        self.cors: CORS = CORS(
            self.app, origins=["http://localhost:3000", "https://ctb-agh.netlify.app"]
        )
        self._setup_endpoints()

        self.cors = CORS(self.app, origins=["http://localhost:3000", "https://ctb-agh.netlify.app"])

    def _create_app(self) -> Flask:
        """Create Flask server."""
        return Flask(self.name)

    def _setup_endpoints(self) -> None:
        """Create endpoints on the Flask server."""
        self.app.add_url_rule("/", view_func=hello_world_endpoint)

        self.api: Blueprint = Blueprint("api", self.name, url_prefix="/api")
        self.v1: Blueprint = Blueprint("v1", self.name, url_prefix="/v1")
        self.v1.register_blueprint(AuthController.blueprint)
        self.v1.register_blueprint(StockMarketController.blueprint)
        self.api.register_blueprint(self.v1)
        self.app.register_blueprint(self.api)

    def launch(self) -> None:
        """Launch the WSGI server."""
        self.server.serve_forever()

    def shutdown(self) -> None:
        """Shutdown the WSGI server."""
        self.server.shutdown()


# app = Flask(__name__)

# api = Blueprint("api", __name__, url_prefix="/api")
# v1 = Blueprint("v1", __name__, url_prefix="/v1")

# v1.register_blueprint(AuthController.blueprint)
# v1.register_blueprint(StockMarketController.blueprint)
# api.register_blueprint(v1)
# app.register_blueprint(api)

# CORS(app, origins=["http://localhost:3000", "https://ctb-agh.netlify.app"])


# app = Server.app  # let Flask figure out what the server is


def hello_world_endpoint() -> str:
    """Root endpoint."""
    return "<p>Hello, World!</p>"
