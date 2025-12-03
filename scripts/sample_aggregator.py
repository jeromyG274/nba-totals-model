#!/usr/bin/env python3
"""Run multiple sampled backtests and aggregate results.
"""
import numpy as np
import pandas as pd
from backtest_1000_fast import generate_1000_games_fast
from src.process import calculate_team_totals
from src.model import predict_total
from src.advanced_stats import get_team_pace_from_espn
from src.injury import adjust_prediction_for_injuries, get_team_injuries
from src.streaks import calculate_streak_adjustment
from src.line_movement import should_filter_based_on_movement
from src.edge import calculate_edge


def run_sample_run(sample_size=200, seed=42):
    np.random.seed(seed)
    all_games = generate_1000_games_fast()
    # sample indices from later portion to ensure training size
    indices = np.random.choice(range(100, 1000), size=sample_size, replace=False)

    pace_map = get_team_pace_from_espn()
    injuries_map = get_team_injuries()

    results = []
    for idx in indices:
        current_game = all_games[idx]
        training_games = all_games[:idx]
        if len(training_games) < 10:
            continue
        try:
            training_df = pd.DataFrame(training_games)
            model_data = calculate_team_totals(training_df)
            if current_game['away'] not in model_data.index or current_game['home'] not in model_data.index:
                continue

            predicted = predict_total(model_data, current_game['away'], current_game['home'], total_multiplier=1.05)
            # Only apply injury adj here (predict_total includes pace/streak)
            injury_adj = adjust_prediction_for_injuries(current_game['away'], current_game['home'], injuries_map)
            predicted += injury_adj

            edge = calculate_edge(predicted, current_game['sportsbook_total'])
            should_bet = should_filter_based_on_movement(predicted, current_game['sportsbook_total'], 'OVER' if edge>0 else 'UNDER')

            actual_total = current_game['total_pts']
            predicted_over = predicted > current_game['sportsbook_total']
            actual_over = actual_total > current_game['sportsbook_total']

            if edge != 0:
                result = "WIN" if (predicted_over and actual_over) or (not predicted_over and not actual_over) else "LOSS"
            else:
                result = "PUSH"

            results.append({
                'home': current_game['home'],
                'away': current_game['away'],
                'predicted': predicted,
                'actual': actual_total,
                'sportsbook': current_game['sportsbook_total'],
                'edge': edge,
                'result': result,
                'filtered': not should_bet,
            })
        except Exception:
            continue

    df = pd.DataFrame(results)
    df_bets = df[df['filtered'] == False]
    wins = len(df_bets[df_bets['result'] == 'WIN'])
    losses = len(df_bets[df_bets['result'] == 'LOSS'])
    pushes = len(df_bets[df_bets['result'] == 'PUSH'])
    bet_games = len(df_bets)
    total_games = len(df)
    win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0.0
    avg_edge = df_bets['edge'].abs().mean() if bet_games > 0 else 0.0
    total_edge = df_bets['edge'].sum() if bet_games > 0 else 0.0

    metrics = {
        'total_games': total_games,
        'bets_placed': bet_games,
        'wins': wins,
        'losses': losses,
        'pushes': pushes,
        'win_rate': win_rate,
        'avg_edge': avg_edge,
        'total_edge': total_edge,
    }

    return metrics, df


if __name__ == '__main__':
    ITER = 10
    SAMPLE_SIZE = 200
    base_seed = 1000

    all_metrics = []
    dfs = []
    for i in range(ITER):
        seed = base_seed + i
        print(f"Running sample {i+1}/{ITER} (seed={seed})")
        metrics, df = run_sample_run(sample_size=SAMPLE_SIZE, seed=seed)
        all_metrics.append(metrics)
        dfs.append(df)
        print(f"  bets: {metrics['bets_placed']}, wins: {metrics['wins']}, win_rate: {metrics['win_rate']:.3f}, avg_edge: {metrics['avg_edge']:.2f}")

    mdf = pd.DataFrame(all_metrics)
    summary = {
        'mean_win_rate': mdf['win_rate'].mean(),
        'std_win_rate': mdf['win_rate'].std(),
        'mean_avg_edge': mdf['avg_edge'].mean(),
        'std_avg_edge': mdf['avg_edge'].std(),
        'mean_bets': mdf['bets_placed'].mean()
    }

    # 95% CI approximate
    n = len(mdf)
    win_ci = (summary['mean_win_rate'] - 1.96 * summary['std_win_rate'] / np.sqrt(n), summary['mean_win_rate'] + 1.96 * summary['std_win_rate'] / np.sqrt(n))
    edge_ci = (summary['mean_avg_edge'] - 1.96 * summary['std_avg_edge'] / np.sqrt(n), summary['mean_avg_edge'] + 1.96 * summary['std_avg_edge'] / np.sqrt(n))

    print('\nAGGREGATED RESULTS')
    print('Runs:', ITER, 'Sample size per run:', SAMPLE_SIZE)
    print(f"Mean win rate: {summary['mean_win_rate']:.3f} (95% CI: {win_ci[0]:.3f} - {win_ci[1]:.3f})")
    print(f"Mean avg edge: {summary['mean_avg_edge']:.2f} (95% CI: {edge_ci[0]:.2f} - {edge_ci[1]:.2f})")
    print(f"Mean bets placed per run: {summary['mean_bets']:.1f}")

    # save detailed results
    out = pd.concat(dfs, ignore_index=True)
    out.to_csv('sampled_aggregated_results.csv', index=False)
    pd.DataFrame(all_metrics).to_csv('sampled_aggregated_metrics.csv', index=False)
    print('\nSaved sampled_aggregated_results.csv and sampled_aggregated_metrics.csv')
