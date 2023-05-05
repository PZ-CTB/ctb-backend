from datetime import date, timedelta
from typing import Optional

import requests

from .. import QUERIES
from . import DatabaseProvider


class DatabaseUpdater:
    """Class for updating the database with new stock matket data."""

    @staticmethod
    def daily_database_update() -> None:
        """Update the database with prices up to the current day."""
        today_date: date = date.today()
        last_known_date: date = DatabaseUpdater.check_last_known_date()
        print(f"DEBUG: Daily database update triggered. Today is {today_date}.")

        if today_date == last_known_date:
            print("DEBUG: Nothing to update.")

        while last_known_date < today_date:
            current_date: date = last_known_date + timedelta(days=1)
            print(f"DEBUG: Updating price for {current_date}.")
            DatabaseUpdater.update_selected_date(current_date)
            last_known_date = DatabaseUpdater.check_last_known_date()

    @staticmethod
    def check_last_known_date() -> date:
        """Check the date of last known price."""
        with DatabaseProvider.handler() as handler:
            handler().execute(QUERIES.SELECT_LAST_KNOWN_DATE)
            last_known_date: date = handler().fetchall()[0][0].date()
            print(last_known_date)
            return last_known_date

    @staticmethod
    def update_selected_date(selected_date: date) -> None:
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
