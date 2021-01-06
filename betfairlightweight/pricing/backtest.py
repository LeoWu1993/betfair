import numpy as np
import pandas as pd
from typing import List, Tuple, Union
from betfairlightweight.database.db_wrapper import PgConnector
from betfairlightweight.utils import SELECTION_NAME_MAPPING, list_to_str, \
    map_market_id_to_selection_names, market_pregame_odds, \
    map_market_id_to_match_stats, return_market_ids_of_selection, map_match_stats_to_market_id
from naive_pricing import calculate_theoretical_probs
from datetime import datetime, timedelta
STAKE_NOTIONAL = 100
WIN_NOTIONAL = 100
RESULT_MAPPING = {'H': [1, 0, 0],
                  'D': [0, 1, 0],
                  'A': [0, 0, 1]}

def generate_signal(odds: np.array, theoretical_probs: np.array, edge_thres = 0.1) -> np.array:
    odds = np.array(odds)
    theoretical_probs = np.array(theoretical_probs)
    implied_prob = 1 / odds
    edge = theoretical_probs - implied_prob
    out = np.zeros(3)
    if max(np.abs(edge)) > edge_thres:
        mask = np.abs(edge) == max(np.abs(edge))
        if edge[mask] > 0:
            out[mask] = 1
        else:
            out[mask] = -1
    return out


def calculate_pnl(odds: np.array, signal: np.array, result: str, same_stake: bool = True) -> float:
    signal = np.array(signal)
    bet = odds * signal
    # bet is somthing like [3, 0, 0] or [0, 0, -4]
    result = np.array(RESULT_MAPPING[result])
    bet_mask = bet != 0
    if np.sum(bet_mask) > 0:
        if bet[bet_mask] > 0: #back
            if result[bet_mask] == 1: #back wins
                if same_stake:
                    return (bet[bet_mask][0] - 1) * STAKE_NOTIONAL
                else:
                    return WIN_NOTIONAL
            else:
                if same_stake:
                    return -STAKE_NOTIONAL
                else:
                    return -WIN_NOTIONAL / (bet[bet_mask][0] - 1)
        elif bet[bet_mask] < 0: #lay
            if result[bet_mask] == 0: #lay wins
                if same_stake:
                    return STAKE_NOTIONAL / (-bet[bet_mask][0] - 1)
                else:
                    return WIN_NOTIONAL
            else:
                if same_stake:
                    return -STAKE_NOTIONAL
                else:
                    return -WIN_NOTIONAL * (-bet[bet_mask][0] - 1)
    else:
        return 0

class BackTest:

    def __init__(self, from_date='2020-01-01', lookback=750, comp='premier_league', same_stake=True, edge_thres=0.1):
        self.from_date = from_date
        self.lookback = lookback
        self.comp = comp
        self.pricing = calculate_theoretical_probs
        self.same_stake = same_stake
        self.edge_thres = edge_thres

    def get_data(self):
        qr = f"select hometeam, awayteam, date, ftr from betfair.match_stats where date>='{self.from_date}' " \
             f"and comp='{self.comp}'"
        data = PgConnector().execute_query(query=qr)
        data = pd.DataFrame(data, columns=['hometeam', 'awayteam', 'date', 'ftr'])
        for i in data.index:
            data.loc[i, 'market_id'] = map_match_stats_to_market_id(data.loc[i, 'hometeam'],
                                                                    data.loc[i, 'awayteam'],
                                                                    data.loc[i, 'date'])
        data.dropna(inplace=True)
        data.reset_index(inplace=True, drop=True)
        self.data = data

    def run_back_test(self):
        self.get_data()
        for i in self.data.index:
            market_id = self.data.loc[i, 'market_id']
            odds = market_pregame_odds(market_id=market_id)


            to_date = pd.to_datetime(self.data.loc[i, 'date']).date() - timedelta(days=10)
            from_date = to_date - timedelta(days=self.lookback)
            home_select, away_select = map_market_id_to_selection_names(market_id=market_id)
            theo = self.pricing(home_selection_name=home_select, away_selection_name=away_select,
                                from_date=str(from_date), to_date=str(to_date), print_odds=False)

            signal = generate_signal(odds=odds, theoretical_probs=theo, edge_thres=self.edge_thres)
            pnl = calculate_pnl(odds=odds, signal=signal, result=self.data.loc[i, 'ftr'], same_stake=self.same_stake)
            self.data.loc[i, 'pnl'] = pnl
            #metric = odds * signal * np.array(RESULT_MAPPING[self.data.loc[i, 'ftr']])
            #self.data.loc[i, 'home_odd'], self.data.loc[i, 'draw_odd'], self.data.loc[i, 'away_odd'] = metric
        return self.data

obj = BackTest()
out = obj.run_back_test()












