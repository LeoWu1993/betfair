import numpy as np
import requests
import datetime
from typing import Optional, List, Tuple
import pandas as pd
from typing import List, Tuple, Union
from betfairlightweight.database.db_wrapper import PgConnector
from database.db_wrapper import PgConnector
from betfairlightweight.compat import BETFAIR_DATE_FORMAT
from betfairlightweight.exceptions import StatusCodeError
from betfairlightweight.__version__ import __title__, __version__

TICK_SIZES = {
    1.0: 0.01,
    2.0: 0.02,
    3.0: 0.05,
    4.0: 0.1,
    6.0: 0.2,
    10.0: 0.5,
    20.0: 1.0,
    30.0: 2.0,
    50.0: 5.0,
    100.0: 10.0,
    1000.0: 1000,
}

SELECTION_NAME_MAPPING = {
    'Tottenham': 'Tottenham',
    'Birmingham': 'Birmingham',
    'Everton': 'Everton',
    'West Brom': 'West Brom',
    'Burnley': 'Burnley',
    'Hull': 'Hull',
    'Huddersfield': 'Huddersfield',
    'Leeds': 'Leeds',
    'Leicester': 'Leicester',
    'Blackburn': 'Blackburn',
    'Liverpool': 'Liverpool',
    'Bournemouth': 'Bournemouth',
    'Blackpool': 'Blackpool',
    'Cardiff': 'Cardiff',
    'Brighton': 'Brighton',
    'Wigan': 'Wigan',
    'Watford': 'Watford',
    'QPR': 'QPR',
    'Fulham': 'Fulham',
    'West Ham': 'West Ham',
    'Reading': 'Reading',
    'Wolves': 'Wolves',
    'Crystal Palace': 'Crystal Palace',
    'Chelsea': 'Chelsea',
    'Stoke': 'Stoke',
    'Newcastle': 'Newcastle',
    'Man City': 'Man City',
    'Norwich': 'Norwich',
    'Swansea': 'Swansea',
    'Sunderland': 'Sunderland',
    'Aston Villa': 'Aston Villa',
    'Arsenal': 'Arsenal',
    'Southampton': 'Southampton',
    'Bolton': 'Bolton',
    'Middlesbrough': 'Middlesbrough',
    'Man Utd': 'Man United',
    'Sheff Utd': 'Sheffield United'
}


def check_status_code(response: requests.Response, codes: list = None) -> None:
    """
    Checks response.status_code is in codes.

    :param requests.request response: Requests response
    :param list codes: List of accepted codes or callable
    :raises: StatusCodeError if code invalid
    """
    codes = codes or [200]
    if response.status_code not in codes:
        raise StatusCodeError(response.status_code)


def clean_locals(data: dict) -> dict:
    """
    Clean up locals dict, remove empty and self/session/params params
    and convert to camelCase.

    :param {} data: locals dicts from a function.
    :returns: dict
    """
    if data.get("params") is not None:
        return data.get("params")
    else:
        return {
            to_camel_case(k): v
            for k, v in data.items()
            if v is not None and k not in ["self", "session", "params", "lightweight"]
        }


def to_camel_case(snake_str: str) -> str:
    """
    Converts snake_string to camelCase

    :param str snake_str:
    :returns: str
    """
    components = snake_str.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def default_user_agent():
    return "{0}/{1}".format(__title__, __version__)


def create_date_string(date: datetime.datetime) -> Optional[str]:
    """
    Convert datetime to betfair
    date string.
    """
    if date:
        return date.strftime(BETFAIR_DATE_FORMAT)

def list_to_str(lis: List) -> str:
    return ','.join(lis)

def return_selection_name(teamname: str):
    ans = teamname
    for i, v in SELECTION_NAME_MAPPING.items():
        if v == teamname:
            ans = i
    return ans

def map_market_id_to_match_stats(market_id) -> List:
    qr = f"select distinct(eventname) from betfair.runner_definitions where market_id = {market_id}"
    event = PgConnector().execute_query(query=qr)[0][0]
    qr = f"select max(markettime) from betfair.runner_definitions where market_id = {market_id}"
    markettime = PgConnector().execute_query(query=qr)[0][0]

    teams = event.split(' v ')
    hometeam, awayteam = teams[0], teams[1]
    try:
        home = SELECTION_NAME_MAPPING[hometeam]
    except:
        home = hometeam
    try:
        away = SELECTION_NAME_MAPPING[awayteam]
    except:
        away = awayteam
    date = str(pd.to_datetime(markettime).date())
    return [home, away, date]

def map_match_stats_to_market_id(home: str, away: str, date: str) -> float:
    home_select = return_selection_name(home)
    away_select = return_selection_name(away)
    eventname = ' v '.join([home_select,away_select])
    qr = f"select distinct(market_id) from betfair.runner_definitions where eventname='{eventname}' " \
         f"and cast(timestamp as varchar) ~ '^{date}'"
    out = PgConnector().execute_query(query=qr)
    if len(out) == 1:
        return out[0][0]
    else:
        return np.nan

def map_market_id_to_selection_names(market_id) -> List:
    qr = f"select distinct(eventname) from betfair.runner_definitions where market_id = {market_id}"
    event = PgConnector().execute_query(query=qr)[0][0]
    qr = f"select max(markettime) from betfair.runner_definitions where market_id = {market_id}"
    teams = event.split(' v ')
    hometeam, awayteam = teams[0], teams[1]
    return [hometeam, awayteam]


def return_market_ids_of_selection(selection_name: str, home: bool) -> List[List]:
    qr = f"select distinct(market_id), eventName from betfair.runner_definitions where "\
         f"selection_name = '{selection_name}'"
    if home is not None:
        if home:
            qr += f"and eventName ~ '^{selection_name}'"
        else:
            qr += f"and eventName ~ '{selection_name}$'"
    out = PgConnector().execute_query(query=qr)
    return out


def selection_pregame_odds(market_id: float, selection_name: str, is_last: bool = True) -> float:
    qr = f"select price from betfair.runner_prices where market_id={market_id} and name='{selection_name}' " \
         f"and timestamp < (select min(timestamp) from betfair.runner_definitions where market_id={market_id} and " \
         f"selection_name='{selection_name}' and inplay=1 group by inplay) order by timestamp"
    out = PgConnector().execute_query(query=qr)
    if len(out):
        if is_last:
            return out[-1][0]
        else:
            return np.mean([i[0] for i in out])[0]
    else:
        print(str(market_id) + 'does not have prices')
        return np.nan

def market_pregame_odds(market_id: float) -> pd.DataFrame:
    hometeam, awayteam = map_market_id_to_selection_names(market_id=market_id)
    qr = f"select timestamp, name, price from betfair.runner_prices where market_id={market_id} and " \
         f"name in {tuple([hometeam,awayteam,'The Draw'])} " \
         f"and timestamp < (select min(timestamp) from betfair.runner_definitions where market_id={market_id} and " \
         f"selection_name='{hometeam}' and inplay=1 group by inplay) order by timestamp"
    out = PgConnector().execute_query(query=qr)
    out = pd.DataFrame(out, columns=['timestamp', 'name', 'price'])
    mask = out.groupby('timestamp')['name'].transform('count') == 3
    out = out[mask].groupby('name').last()
    [home_select, away_select] = map_market_id_to_selection_names(market_id)
    out = out.loc[[home_select, 'The Draw', away_select], 'price'].values
    return out

def list_selection_pregame_odds(selection_name: str, home: bool) -> pd.DataFrame:
    tmp = return_market_ids_of_selection(selection_name, home)
    market_ids, event_names = [i[0] for i in tmp], [i[1] for i in tmp]
    ans = np.zeros(len(market_ids))
    for i, m in enumerate(market_ids):
        ans[i] = selection_pregame_odds(market_id=m, selection_name=selection_name)
    ans = pd.DataFrame({'market_id': market_ids, 'event_name': event_names, 'price': ans})
    ans.sort_values(by=['price'], inplace=True)
    return ans

