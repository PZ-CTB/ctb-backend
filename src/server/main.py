from flask import Blueprint, Flask
from flask_cors import CORS

from .auth import AuthController
from .database import DatabaseProvider
from .stock_market import StockMarketController

DatabaseProvider.initialize()

app = Flask(__name__)

api = Blueprint("api", __name__, url_prefix="/api")
v1 = Blueprint("v1", __name__, url_prefix="/v1")

v1.register_blueprint(AuthController.blueprint)
v1.register_blueprint(StockMarketController.blueprint)
api.register_blueprint(v1)
app.register_blueprint(api)

CORS(app, origins=["http://localhost:3000", "https://ctb-agh.netlify.app"])


@app.route("/")
def hello_world() -> str:
    """Root endpoint."""
    return "<p>Hello, World!</p>"
