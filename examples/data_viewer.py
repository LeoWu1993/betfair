import pandas as pd
import json
from bz2 import BZ2File

PATH = "C:/Users/Leo/PycharmProjects/betfair1/data/"
file_name = "28130778.bz2"


def parse_bz_file(input_file_name: str) -> pd.DataFrame:
    with BZ2File(PATH + input_file_name, "r") as f:
        lines = f.readlines()

    price_changes = []

    for line in lines:
        content = json.loads(line)
        market_changes = content.get("mc", [])
        for market_change in market_changes:
            market_id = market_change.get("id")
            market_definition = market_change.get("marketDefinition")

            runner_changes = market_change.get("rc")
            if runner_changes:
                for runner_change in runner_changes:
                    print(runner_change)
                    price_changes.append([content.get("pt"), runner_change.get("id"), runner_change.get("ltp")])

    df = pd.DataFrame(price_changes, columns=["timestamp", "selection_id", "price"])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    return df

df = parse_bz_file(file_name)
print('hi')
