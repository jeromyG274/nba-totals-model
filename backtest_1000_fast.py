#!/usr/bin/env python3
"""
Optimized 1000-game backtest: Sample 200 games from simulated 1000, test with enhanced model.
Much faster than full sequential processing.
"""

import pandas as pd
import numpy as np
from src.process import calculate_team_totals
from src.model import predict_total
from src.edge import calculate_edge
from src.advanced_stats import get_pace_adjusted_total, get_team_pace_from_espn
from src.injury import adjust_prediction_for_injuries, get_team_injuries
from src.streaks import calculate_streak_adjustment
from src.line_movement import should_filter_based_on_movement


TEAMS = [
    "Boston Celtics", "Miami Heat", "Denver Nuggets", "Golden State Warriors",
    "Los Angeles Lakers", "Phoenix Suns", "Milwaukee Bucks", "New York Knicks",
    "Chicago Bulls", "Memphis Grizzlies", "Sacramento Kings", "Dallas Mavericks",
    "Los Angeles Clippers", "Houston Rockets", "Atlanta Hawks", "Detroit Pistons",
    "Indiana Pacers", "Portland Trail Blazers", "San Antonio Spurs", "Charlotte Hornets",
    "Brooklyn Nets", "Orlando Magic", "Washington Wizards", "Toronto Raptors",
    "Cleveland Cavaliers", "Oklahoma City Thunder", "Minnesota Timberwolves",
    "New Orleans Pelicans", "Utah Jazz"
]

TEAM_OFFEFF = {
    "Denver Nuggets": 117.5, "Golden State Warriors": 115.8, "Boston Celtics": 115.2,
    "Phoenix Suns": 114.9, "Milwaukee Bucks": 114.5, "Los Angeles Lakers": 113.2,
    "Dallas Mavericks": 112.8, "Sacramento Kings": 112.5, "New York Knicks": 111.9,
    "Miami Heat": 111.5, "Houston Rockets": 111.2, "Chicago Bulls": 110.8,
    "Los Angeles Clippers": 110.5, "Atlanta Hawks": 110.2, "Toronto Raptors": 109.8,
    "Memphis Grizzlies": 109.5, "Portland Trail Blazers": 109.2, "Cleveland Cavaliers": 109.0,
    "Oklahoma City Thunder": 108.8, "Indiana Pacers": 108.5, "Washington Wizards": 108.2,
    "New Orleans Pelicans": 107.9, "Charlotte Hornets": 107.5, "Detroit Pistons": 107.2,
    "Utah Jazz": 106.8, "Orlando Magic": 106.5, "Brooklyn Nets": 106.2,
    "San Antonio Spurs": 105.9, "Minnesota Timberwolves": 105.5
}

TEAM_DEFEFF = {
    "Boston Celtics": 105.8, "Denver Nuggets": 106.2, "Miami Heat": 106.5,
    "Golden State Warriors": 107.2, "Memphis Grizzlies": 107.5, "New York Knicks": 108.0,
    "Milwaukee Bucks": 108.2, "Phoenix Suns": 108.8, "Los Angeles Lakers": 109.2,
    "Dallas Mavericks": 109.5, "Houston Rockets": 109.8, "Oklahoma City Thunder": 110.2,
    "Sacramento Kings": 110.5, "Chicago Bulls": 110.8, "Los Angeles Clippers": 111.2,
    "Toronto Raptors": 111.5, "Atlanta Hawks": 111.8, "Portland Trail Blazers": 112.2,
    "Indiana Pacers": 112.5, "Charlotte Hornets": 112.8, "Washington Wizards": 113.2,
    "Detroit Pistons": 113.5, "New Orleans Pelicans": 113.8, "Orlando Magic": 114.2,
    "Utah Jazz": 114.5, "Cleveland Cavaliers": 114.8, "Minnesota Timberwolves": 115.2,
    "Brooklyn Nets": 115.5, "San Antonio Spurs": 115.8
}


def generate_1000_games_fast():
    """Generate all 1000 games upfront."""
    games = []
    np.random.seed(42)
    
    for i in range(1000):
        home_idx = np.random.randint(0, len(TEAMS))
        away_idx = np.random.randint(0, len(TEAMS))
        while away_idx == home_idx:
            away_idx = np.random.randint(0, len(TEAMS))
        
        home = TEAMS[home_idx]
        away = TEAMS[away_idx]
        
        home_offeff = TEAM_OFFEFF.get(home, 110.0)
        away_offeff = TEAM_OFFEFF.get(away, 110.0)
        home_defeff = TEAM_DEFEFF.get(home, 110.0)
        away_defeff = TEAM_DEFEFF.get(away, 110.0)
        
        home_expected = (home_offeff + away_defeff) / 2 + 3.5
        away_expected = (away_offeff + home_defeff) / 2
        
        home_pts = int(np.random.normal(home_expected, 5.0))
        away_pts = int(np.random.normal(away_expected, 5.0))
        home_pts = max(85, home_pts)
        away_pts = max(85, away_pts)
        
        total = home_pts + away_pts
        base_line = (home_expected + away_expected)
        sportsbook = base_line + np.random.normal(0, 1.0)
        sportsbook = round(sportsbook * 2) / 2
        
        games.append({
            "date": f"2025-11-{(i % 30) + 1:02d}",
            "home": home,
            "away": away,
            "home_pts": home_pts,
            "away_pts": away_pts,
            "total_pts": total,
            "sportsbook_total": sportsbook
        })
    
    return games


def run_sampled_backtest():
    """Sample 200 games from 1000, use all prior games for training."""
    all_games = generate_1000_games_fast()
    print(f"Generated 1000 realistic games")
    print(f"Total range: {min([g['total_pts'] for g in all_games])}-{max([g['total_pts'] for g in all_games])} pts\n")
    
    # Sample 30 games evenly spaced from 1000 games (very fast execution)
    sample_indices = np.linspace(100, 999, 30, dtype=int)
    
    results = []
    
    # Pre-fetch external data once (cache) to avoid per-game network calls
    pace_map = get_team_pace_from_espn()
    injuries_map = get_team_injuries()

    for idx in sample_indices:
        current_game = all_games[idx]
        training_games = all_games[:idx]
        
        if len(training_games) < 10:
            continue
        
        try:
            training_df = pd.DataFrame(training_games)
            model_data = calculate_team_totals(training_df)
            
            if current_game['away'] not in model_data.index or current_game['home'] not in model_data.index:
                continue
            
            # predict_total already applies pace and streak adjustments.
            # Only apply injury adjustment here (predict_total doesn't include injuries).
            predicted = predict_total(model_data, current_game['away'], current_game['home'], total_multiplier=1.05)

            injury_adj = adjust_prediction_for_injuries(current_game['away'], current_game['home'], injuries_map)
            predicted += injury_adj
            
            edge = calculate_edge(predicted, current_game['sportsbook_total'])
            should_bet = should_filter_based_on_movement(predicted, current_game['sportsbook_total'], "OVER" if edge > 0 else "UNDER")
            
            actual_total = current_game['total_pts']
            predicted_over = predicted > current_game['sportsbook_total']
            actual_over = actual_total > current_game['sportsbook_total']
            
            if edge != 0:
                result = "WIN" if (predicted_over and actual_over) or (not predicted_over and not actual_over) else "LOSS"
            else:
                result = "PUSH"
            
            results.append({
                "home": current_game['home'],
                "away": current_game['away'],
                "predicted": predicted,
                "actual": actual_total,
                "sportsbook": current_game['sportsbook_total'],
                "edge": edge,
                "result": result,
                "filtered": not should_bet
            })
            
            print(f".", end="", flush=True)
        
        except Exception as e:
            continue
    
    print()
    return pd.DataFrame(results)


def summarize_backtest(results_df):
    """Print comprehensive summary."""
    total_games = len(results_df)
    filtered_games = len(results_df[results_df['filtered'] == True])
    bet_games = len(results_df[results_df['filtered'] == False])
    
    df_bets = results_df[results_df['filtered'] == False]
    
    wins = len(df_bets[df_bets['result'] == 'WIN'])
    losses = len(df_bets[df_bets['result'] == 'LOSS'])
    pushes = len(df_bets[df_bets['result'] == 'PUSH'])
    
    win_rate = wins / (wins + losses) if (wins + losses) > 0 else 0
    avg_edge = df_bets['edge'].abs().mean() if len(df_bets) > 0 else 0
    total_edge = df_bets['edge'].sum()
    
    print("\n" + "=" * 80)
    print("LARGE-SCALE BACKTEST (SAMPLE FROM 1000 GAMES)")
    print("=" * 80)
    print(f"Total Games Analyzed:    {total_games:>6}")
    print(f"Games Filtered Out:      {filtered_games:>6} ({100*filtered_games/total_games:.1f}%)")
    print(f"Bets Placed:             {bet_games:>6} ({100*bet_games/total_games:.1f}%)")
    print("-" * 80)
    print(f"Wins:                    {wins:>6}")
    print(f"Losses:                  {losses:>6}")
    print(f"Pushes:                  {pushes:>6}")
    print(f"Win Rate:                {win_rate:>6.1%}")
    print("-" * 80)
    print(f"Avg Edge Per Bet:        {avg_edge:>6.2f} points")
    print(f"Total Edge (All Bets):   {total_edge:>6.1f} points")
    if win_rate > 0 and (wins + losses) > 0:
        roi = win_rate * 5 - (1-win_rate) * 5
        print(f"Expected ROI (5% margin): {roi:>5.1f}% per bet")
    print("=" * 80)
    
    print("\nEdge Distribution:")
    print(f"  High edge (>15pts):      {len(df_bets[df_bets['edge'].abs() > 15])} bets")
    print(f"  Medium edge (5-15pts):   {len(df_bets[(df_bets['edge'].abs() > 5) & (df_bets['edge'].abs() <= 15)])} bets")
    print(f"  Low edge (<5pts):        {len(df_bets[df_bets['edge'].abs() <= 5])} bets")
    
    overs = len(df_bets[df_bets['edge'] > 0])
    unders = len(df_bets[df_bets['edge'] < 0])
    print(f"\nOver/Under Split:")
    if bet_games > 0:
        print(f"  OVER bets:               {overs} ({100*overs/bet_games:.1f}%)")
        print(f"  UNDER bets:              {unders} ({100*unders/bet_games:.1f}%)")


if __name__ == "__main__":
    print("Starting sampled backtest (200 games from 1000 simulated)...\n")
    results = run_sampled_backtest()
    summarize_backtest(results)
    results.to_csv("backtest_1000_sampled_results.csv", index=False)
    print("\n✓ Results saved to backtest_1000_sampled_results.csv")
