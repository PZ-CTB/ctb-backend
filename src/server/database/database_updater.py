import logging
from datetime import date, timedelta
from typing import Optional

import requests
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from .. import QUERIES
from . import DatabaseProvider


class DatabaseUpdater:
    """Class for updating the database with new stock matket data."""

    scheduler: Optional[BackgroundScheduler] = None

    @classmethod
    def initialize(cls) -> None:
        """Initialize DatabaseUpdater."""
        cls.scheduler = BackgroundScheduler()
        cls.scheduler.start()

        def scheduled_tasks() -> None:
            DatabaseUpdater.daily_database_update()

        cls.scheduler.add_job(
            func=scheduled_tasks,
            trigger=CronTrigger(hour=6, minute=0, second=0),
            max_instances=1,
        )

    @staticmethod
    def daily_database_update() -> None:
        """Update the database with prices up to the current day."""
        today_date: date = date.today()
        last_known_date: Optional[date] = DatabaseUpdater._get_last_known_date()
        if last_known_date is None:
            return
        logging.debug(f"Daily database update triggered. Today is {today_date}.")

        if today_date == last_known_date:
            logging.debug("Nothing to update.")

        while last_known_date < today_date:
            current_date: date = last_known_date + timedelta(days=1)
            logging.debug(f"Updating price for {current_date}.")
            DatabaseUpdater._update_selected_date(current_date)
            last_known_date += timedelta(days=1)

    @staticmethod
    def _get_last_known_date() -> Optional[date]:
        """Check the date of last known price."""
        last_known_date: Optional[date] = None

        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_LAST_KNOWN_DATE)
            last_known_date = handler().fetchall()[0][0].date()

        if not handler.success:
            return None

        logging.debug(f"{last_known_date=}")
        return last_known_date

    @staticmethod
    def _update_selected_date(selected_date: date) -> bool:
        """Fetch price for chosen date and put it in the database."""
        date_string_dmy: str = selected_date.strftime("%d-%m-%Y")
        url = f"https://api.coingecko.com/api/v3/coins/bitcoin/history?date={date_string_dmy}"
        response = requests.get(url)
        price: float = float(response.json()["market_data"]["current_price"]["usd"])

        date_string_ymd: str = selected_date.strftime("%Y-%m-%d")
        with DatabaseProvider.handler() as handler:
            handler().execute(
                QUERIES.INSERT_PRICE,
                (
                    date_string_ymd,
                    price,
                ),
            )

        if handler.success:
            return True

        logging.debug("Price insertion failed")
        return False
