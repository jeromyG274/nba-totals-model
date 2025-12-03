#!/usr/bin/env python3
"""Diagnostic: reproduce prediction components for sampled games and print breakdown."""
import sys
from pathlib import Path
# Add project root to sys.path so top-level modules can be imported
ROOT = str(Path(__file__).resolve().parents[1])
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from backtest_1000_fast import generate_1000_games_fast, np
import pandas as pd
from src.process import calculate_team_totals
from src.model import predict_total
from src.advanced_stats import get_team_pace_from_espn, get_pace_adjusted_total
from src.injury import adjust_prediction_for_injuries, get_team_injuries
from src.streaks import calculate_streak_adjustment
from src.line_movement import should_filter_based_on_movement
from src.edge import calculate_edge


def diagnostic(n=30):
    all_games = generate_1000_games_fast()
    sample_indices = np.linspace(100, 999, n, dtype=int)

    pace_map = get_team_pace_from_espn()
    injuries_map = get_team_injuries()

    rows = []
    for idx in sample_indices:
        game = all_games[idx]
        training = all_games[:idx]
        if len(training) < 10:
            continue
        df = pd.DataFrame(training)
        model_data = calculate_team_totals(df)
        if game['away'] not in model_data.index or game['home'] not in model_data.index:
            continue

        # Recompute base components (matching src.model.predict_total logic up to before pace/streak)
        league_avg_scored = 110
        league_avg_allowed = 110
        home = model_data.loc[game['home']]
        away = model_data.loc[game['away']]

        home_scored = home.get('avg_scored_home', league_avg_scored) or league_avg_scored
        home_allowed = home.get('avg_allowed_home', league_avg_allowed) or league_avg_allowed
        away_scored = away.get('avg_scored_away', league_avg_scored) or league_avg_scored
        away_allowed = away.get('avg_allowed_away', league_avg_allowed) or league_avg_allowed

        base_pred = (home_scored + away_scored + home_allowed + away_allowed) / 2
        hc_bonus = 3.5
        base_pred = base_pred + hc_bonus
        base_pred = base_pred * 1.05  # total_multiplier

        # pace adj computed from base_pred
        pace_adj = get_pace_adjusted_total(base_pred, game['away'], game['home'], pace_map)

        # streak adj
        streak_adj = calculate_streak_adjustment(game['home'], game['away'])

        # injury adj
        injury_adj = adjust_prediction_for_injuries(game['away'], game['home'], injuries_map)

        # recomposed final
        recomposed = round(base_pred + pace_adj + streak_adj + injury_adj, 1)

        # predict_total result
        pred_direct = predict_total(model_data, game['away'], game['home'], total_multiplier=1.05)
        # note: predict_total does not include injury; so add injury_adj to compare
        pred_direct_plus_injury = round(pred_direct + injury_adj, 1)

        sportsbook = game['sportsbook_total']
        edge = calculate_edge(recomposed, sportsbook)
        should_bet = should_filter_based_on_movement(recomposed, sportsbook, 'OVER' if edge>0 else 'UNDER')

        rows.append({
            'idx': idx,
            'home': game['home'],
            'away': game['away'],
            'base_pred': round(base_pred,1),
            'pace_adj': round(pace_adj,2),
            'streak_adj': round(streak_adj,2),
            'injury_adj': round(injury_adj,2),
            'recomposed_final': recomposed,
            'predict_total_direct': pred_direct,
            'predict_total_plus_injury': pred_direct_plus_injury,
            'sportsbook': sportsbook,
            'edge': round(edge,2),
            'filtered': not should_bet,
            'actual': game['total_pts']
        })

    dfout = pd.DataFrame(rows)
    pd.set_option('display.max_columns', None)
    print(dfout)
    dfout.to_csv('diagnostic_preds.csv', index=False)
    print('\nSaved diagnostic_preds.csv')


if __name__ == '__main__':
    diagnostic()
