import datetime

import requests
from matplotlib import pyplot as plt

first_date = datetime.datetime(2021, 7, 7)
end_date = datetime.datetime.now()
print(first_date)

from_timestamp = int(first_date.timestamp())
end_timestamp = int(end_date.timestamp())
end_timestamp = end_timestamp - (end_timestamp % (60 * 60 * 24))
print(from_timestamp)
print(end_timestamp)

url = f"https://api.coingecko.com/api/v3/coins/bitcoin/market_chart/range?vs_currency=usd&from={from_timestamp}&to={end_timestamp}"
response = requests.get(url)

prices = response.json()["prices"]
print(prices)

query_components = [
    (
        datetime.datetime.fromtimestamp(entry[0] / 1000).strftime("%Y-%m-%d"),
        int(entry[0] / 1000),
        entry[1],
    )
    for entry in prices
]

with open("updated_prices.sql", "w") as file:
    file.write("INSERT INTO exchange_rate_history (date, value) VALUES\n")
    separator = ","
    for date, timestamp, price in query_components:
        if timestamp == query_components[len(query_components) - 1][1]:
            separator = ";"
        file.write(f"('{date}', {price}){separator}\n")
