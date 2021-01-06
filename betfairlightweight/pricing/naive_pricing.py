import numpy as np
import pandas as pd
from betfairlightweight.database.db_wrapper import PgConnector
from betfairlightweight.utils import SELECTION_NAME_MAPPING, list_to_str

OPPO_COL = {
    True: 'awayteam',
    False: 'hometeam'
}

TEAM_CLUSTERS_MAPPING = {
    'Liverpool': 1,
    'Man Utd': 1,
    'Man City': 1,
    'Tottenham': 1,
    'Chelsea': 1,
    'Arsenal': 1,
    'Wolves': 2,
    'Leicester': 2,
    'Everton': 2,
    'West Ham': 2,
}

def team_cluster_mapping(selection_name: str):
    if selection_name in TEAM_CLUSTERS_MAPPING:
        return TEAM_CLUSTERS_MAPPING[selection_name]
    else:
        return max([v for v in TEAM_CLUSTERS_MAPPING.values()]) + 1


def list_game_results(selection_name: str, home: bool, from_date = None, to_date = None) -> pd.DataFrame:
    try:
        match_game = SELECTION_NAME_MAPPING[selection_name]
    except:
        match_game = selection_name
    if home:
        cols_out = ['date', 'time', 'awayteam', 'ftr']
        qr = f"select {list_to_str(cols_out)} from betfair.match_stats where hometeam = '{match_game}'"
    else:
        cols_out = ['date', 'time', 'hometeam', 'ftr']
        qr = f"select {list_to_str(cols_out)} from betfair.match_stats where awayteam = '{match_game}'"
    if from_date is not None:
        qr += f" and date >= '{from_date}'"
    if to_date is not None:
        qr += f" and date <= '{to_date}'"
    out = PgConnector().execute_query(query=qr)
    out = pd.DataFrame(out, columns=cols_out)
    if home:
        out['ftr'] = out['ftr'].map({'H': 1, 'A': -1, 'D': 0})
    else:
        out['ftr'] = out['ftr'].map({'A': 1, 'H': -1, 'D': 0})
    return out

def summarize_game_results(selection_name: str, home: bool, is_cluster: bool = True, from_date = None, to_date = None)\
        -> pd.DataFrame:
    out = list_game_results(selection_name=selection_name, home=home, from_date=from_date, to_date=to_date)
    if is_cluster:
        out['team_cluster'] = out[OPPO_COL[home]].map(team_cluster_mapping)
        res = out.groupby(['team_cluster','ftr'])['date'].count()/out.groupby(['team_cluster'])['date'].count()
        res = res.unstack()
        res = res.replace(np.nan, 0)
    else:
        res = out.groupby(['ftr'])['date'].count()/out.shape[0]
    return res

def calculate_theoretical_probs(home_selection_name: str, away_selection_name: str, print_odds: bool = True,
                                from_date=None, to_date=None, is_print=False):
    home_cluster = team_cluster_mapping(home_selection_name)
    away_cluster = team_cluster_mapping(away_selection_name)
    home_df = summarize_game_results(selection_name=home_selection_name, home=True,
                                       from_date=from_date, to_date=to_date)
    away_df = summarize_game_results(selection_name=away_selection_name, home=False,
                                       from_date=from_date, to_date=to_date)
    for i in [-1, 0, 1]:
        if i not in home_df.columns:
            home_df[i] = 0
        if i not in away_df.columns:
            away_df[i] = 0
    if away_cluster in home_df.index:
        home_prob = home_df.loc[away_cluster]
        if is_print:
            print(home_selection_name + '\n' + '*' * 50)
            print(home_df)
            print(home_prob)
    else:
        print(home_selection_name + " didnt enounter " + away_selection_name + " team cluster!")
        home_prob = []
    if home_cluster in away_df.index:
        away_prob = away_df.loc[home_cluster]
        if is_print:
            print(away_selection_name + '\n' + '*' * 50)
            print(away_df)
            print(away_prob)
    else:
        print(away_selection_name + " didnt enounter " + home_selection_name + " team cluster!")
        away_prob = []

    if len(home_prob) and len(away_prob):
        out = [home_prob.loc[1] + away_prob.loc[-1], home_prob.loc[0] + away_prob.loc[0],
               home_prob.loc[-1] + away_prob.loc[1]]
    elif len(home_prob):
        out = [home_prob.loc[1], home_prob.loc[0], home_prob.loc[-1]]
    elif len(away_prob):
        out = [away_prob.loc[-1], away_prob.loc[0], away_prob.loc[1]]
    else:
        raise ValueError("Both teams did not meet opponent's team cluster")
    out = out / np.sum(out)
    if print_odds:
        return [1/i if i > 0 else 100 for i in out]
    else:
        return out

print(calculate_theoretical_probs(home_selection_name='Man Utd',away_selection_name='Man City',
                                  from_date='2018-01-01',print_odds=False, is_print=True))
print(summarize_game_results(selection_name='Man Utd',home=True,from_date='2018-01-01',is_cluster=False))
print(summarize_game_results(selection_name='Man City',home=False,from_date='2018-01-01',is_cluster=False))



