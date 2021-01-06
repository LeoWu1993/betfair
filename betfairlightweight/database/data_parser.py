import pandas as pd
import numpy as np
import json
from bz2 import BZ2File
from typing import Tuple, List, Union
import os
import os.path
import logging

from betfairlightweight.database.db_wrapper import PgConnector

BETFAIR_DATA_PATH = "C:/Users/Leo/PycharmProjects/betfair1/data/betfair/2020/"
MATCH_DATA_PATH = "C:/Users/Leo/PycharmProjects/betfair1/data/match_stats/la_liga/"

def parse_definitions(input_file_name: str, cols_out: List = None) -> pd.DataFrame:
    print(input_file_name)
    with BZ2File(input_file_name, "r") as f:
        lines = f.readlines()
    cols_market = ["bspMarket", "turnInPlayEnabled", "persistenceEnabled",
               "eventTypeId", "numberOfWinners", "bettingType",
               "marketType", "marketTime", "suspendTime",
               "bspReconciled", "complete", "inPlay", "crossMatching",
               "runnersVoidable", "numberOfActiveRunners", "betDelay","eventName"
               ]
    cols_runner = ["status", "sortPriority", "id", "name"]
    cols_default = ["marketTime", "suspendTime", "inPlay", "numberOfActiveRunners","eventName"]
    market_definitions = []

    for line in lines:
        content = json.loads(line)
        market_changes = content.get("mc",[])
        for market_change in market_changes:
            if 'marketDefinition' in market_change:
                market_definition = market_change.get('marketDefinition')
                runners = market_definition['runners']
                for runner in runners:
                    market_definitions.append([content.get('pt')] + [market_change.get('id')] +
                                              [market_definition.get(i, np.nan) for i in cols_market] +
                                              [runner.get(i, np.nan) for i in cols_runner])

    df = pd.DataFrame(market_definitions, columns=['timestamp'] + ['market_id'] + cols_market + cols_runner)
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    if cols_out is not None:
        c = cols_out
    else:
        c = ['timestamp', 'market_id'] + cols_default + cols_runner
    return df[c]

def parse_market_prices(input_file_name: str) -> pd.DataFrame:
    with BZ2File(input_file_name, "r") as f:
        lines = f.readlines()

    price_changes = []
    runner_definitions = {}

    for line in lines:
        content = json.loads(line)
        market_changes = content.get("mc",[])
        for market_change in market_changes:
            if 'marketDefinition' in market_change:
                market_definition = market_change.get('marketDefinition')
                runners = market_definition['runners']
                for runner in runners:
                    if runner['id'] not in runner_definitions:
                        runner_definitions[runner['id']] = runner['name']
            elif 'rc' in market_change:
                runner_changes = market_change.get("rc")
                for runner_change in runner_changes:
                    if "hc" not in runner_change:
                        price_changes.append([content.get("pt"), market_change.get("id"),
                                              runner_change.get("id"), runner_change.get("ltp")])

    df = pd.DataFrame(price_changes, columns=["timestamp", "market_id", "selection_id", "price"])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    runner_definitions = pd.Series(runner_definitions).to_frame(name='name')
    out = df.set_index("selection_id").join(runner_definitions).reset_index()
    out.rename(columns={'index': 'selection_id'}, inplace=True)
    return out

def prepare_output(func, unique_key: List = None):
    out = pd.DataFrame()
    for dirpath, dirnames, filenames in os.walk(BETFAIR_DATA_PATH):
        for filename in [f for f in filenames if f.endswith(".bz2")]:
            full_path = os.path.join(dirpath, filename)
            full_path = full_path.replace("\\", "/")
            try:
                tmp = func(full_path)
                out = out.append(tmp)
            except Exception:
                logging.exception(filename + ' failed')
                pass
    out.drop_duplicates(subset=unique_key, keep="first", inplace=True)
    return out

def write_output(out: pd.DataFrame, table_name: str):
    out = [list(out.loc[i]) for i in out.index]
    PgConnector().insert_to_table(out, schema='betfair', table=table_name)

def write_runner_prices(out: pd.DataFrame):
    cols_out = ['market_id', 'selection_id', 'timestamp', 'name', 'price']
    out['selection_id'] = out['selection_id'].astype('float')
    out = out[cols_out]
    out.reset_index(drop=True, inplace=True)
    out = [list(out.loc[i]) for i in out.index]
    PgConnector().insert_to_table(out, schema='betfair', table='runner_prices')

def write_runner_definitions(out: pd.DataFrame):
    out['numberOfActiveRunners'] = out['numberOfActiveRunners'].astype('float')
    out['sortPriority'] = out['sortPriority'].astype('float')
    out['id'] = out['id'].astype('float')
    out['inPlay'] = out['inPlay'] * 1
    out['inPlay'] = out['inPlay'].astype('float')
    out.reset_index(drop=True, inplace=True)
    out = [list(out.loc[i]) for i in out.index]
    PgConnector().insert_to_table(out, schema='betfair', table='runner_definitions')

def write_match_stats(comp: str, cols_out: List = None):
    df = pd.DataFrame()
    default_cols = ['Date', 'Time', 'HomeTeam', 'AwayTeam', 'FTHG', 'FTAG',
                    'FTR', 'HTHG', 'HTAG', 'HTR', 'B365H', 'B365D', 'B365A', 'Comp']
    for filename in os.listdir(MATCH_DATA_PATH):
        if filename.endswith(".csv"):
            # print(os.path.join(directory, filename))
            df = df.append(pd.read_csv(MATCH_DATA_PATH + filename), sort=False)
    df.reset_index(drop=True, inplace=True)
    df['Date'] = pd.to_datetime(df['Date'], dayfirst=True)
    df.dropna(subset=['Date'], inplace=True)
    df['Date'] = df['Date'].dt.strftime('%Y-%m-%d')
    df['Comp'] = comp
    if cols_out is not None:
        df = df[cols_out]
    else:
        df = df[default_cols]
    df['FTHG'] = df['FTHG'].astype('float')
    df['FTAG'] = df['FTAG'].astype('float')
    df['HTHG'] = df['HTHG'].astype('float')
    df['HTAG'] = df['HTAG'].astype('float')
    df = [list(df.loc[i]) for i in df.index]
    PgConnector().insert_to_table(df, schema='betfair', table='match_stats')

write_match_stats('la_liga')



