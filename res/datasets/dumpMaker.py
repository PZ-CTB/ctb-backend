# to jest narzędzie tymczasowe

import pandas as pd

df: pd.DataFrame = pd.read_csv("coin_Bitcoin.csv")

values: list[str] = []

for date, high, low, _open, _close in zip(
    df["Date"], df["High"], df["Low"], df["Open"], df["Close"]
):
    date = date[:10]
    value = sum((high, low, _open, _close)) / 4
    values.append(f"('{date}', {value})")

with open(file="dump.sql", mode="w", encoding="utf-8") as f:
    f.write("INSERT INTO exchange_rate_history (date, value) VALUES\n")
    f.write(",\n".join(values))
    f.write(";")
