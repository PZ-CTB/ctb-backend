from flask import Flask

from src.server import Server


def create_app() -> Flask:
    """Production server launch."""
    server = Server()
    return server.app


if __name__ == "__main__":
    """Debug server launch."""
    server = Server()
    server.launch()
