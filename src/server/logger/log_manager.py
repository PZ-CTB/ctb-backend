import logging
import os
from datetime import datetime
from logging.handlers import RotatingFileHandler

from .. import CONSTANTS


class LogManager:
    """Setup logging for the server."""

    @classmethod
    def initialize(cls) -> None:
        """Initialize logging manager."""
        cls._ensure_log_dir_exists()
        cls._setup_logger_config()
        cls._setup_external_loggers()

    @classmethod
    def _ensure_log_dir_exists(cls) -> None:
        if not os.path.exists(CONSTANTS.LOG_DIRECTORY):
            os.makedirs(CONSTANTS.LOG_DIRECTORY, exist_ok=True)

    @classmethod
    def _setup_logger_config(cls) -> None:
        time_now: str = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        rotating_file_handler: RotatingFileHandler = RotatingFileHandler(
            filename=f"{CONSTANTS.LOG_DIRECTORY}/{CONSTANTS.LOG_LEVEL.lower()}_{time_now}.log",
            maxBytes=1000 * 1000 * 50,  # 50 MB
            backupCount=10,
            encoding="utf-8",
        )

        logging.basicConfig(
            format="%(levelname)s|%(asctime)s|%(name)s|%(filename)s:%(lineno)d|%(funcName)s()| "
            f"%(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            level=CONSTANTS.LOG_LEVEL,
            encoding="utf-8",
            handlers=[rotating_file_handler],
        )

    @classmethod
    def _setup_external_loggers(cls) -> None:
        logging.getLogger("werkzeug").setLevel(logging.INFO)
        logging.getLogger("apscheduler").setLevel(logging.WARNING)
