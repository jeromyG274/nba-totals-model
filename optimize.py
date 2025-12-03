"""
Model optimization script - test different parameters to maximize win rate.
"""
import pandas as pd
from src.backtest import get_historical_games, summarize_backtest
from src.process import calculate_team_totals, calculate_home_court_advantage
from src.edge import calculate_edge


def predict_total_optimized(model_data, away_team, home_team, 
                            home_court_bonuses=None, total_multiplier=1.0):
    """
    Optimized prediction with configurable total multiplier.
    Multiplier scales the entire prediction (e.g., 1.05 = 5% higher totals).
    """
    if home_court_bonuses is None:
        home_court_bonuses = {}
    
    league_avg_scored = 110
    league_avg_allowed = 110
    
    try:
        home = model_data.loc[home_team]
        away = model_data.loc[away_team]
    except KeyError:
        raise ValueError(f"Team not found")
    
    home_scored = home.get("avg_scored_home", league_avg_scored) or league_avg_scored
    home_allowed = home.get("avg_allowed_home", league_avg_allowed) or league_avg_allowed
    away_scored = away.get("avg_scored_away", league_avg_scored) or league_avg_scored
    away_allowed = away.get("avg_allowed_away", league_avg_allowed) or league_avg_allowed
    
    pred = (home_scored + away_scored + home_allowed + away_allowed) / 2
    
    # Apply team-specific home court bonus
    home_bonus = home_court_bonuses.get(home_team, 3.5)
    pred = pred + home_bonus
    
    # Apply total multiplier
    pred = pred * total_multiplier
    
    return round(pred, 1)


def grid_search_backtest():
    """
    Test different total multipliers to find optimal configuration.
    """
    all_games = get_historical_games(30)
    all_games = all_games.sort_values('date').reset_index(drop=True)
    
    results_summary = []
    
    # Test different total multipliers (1.0 = no change, 1.05 = 5% higher, etc.)
    for multiplier in [0.95, 0.98, 1.0, 1.02, 1.05, 1.08, 1.1]:
        results = []
        
        for idx in range(len(all_games)):
            current_game = all_games.iloc[idx]
            training_data = all_games.iloc[:idx]
            
            if len(training_data) < 4:
                continue
            
            try:
                model_data = calculate_team_totals(training_data, recency_weight=True)
                
                if current_game['away'] not in model_data.index or current_game['home'] not in model_data.index:
                    continue
                
                # Get team-specific home court advantages
                home_court_bonuses = calculate_home_court_advantage(model_data)
                
                predicted = predict_total_optimized(
                    model_data,
                    current_game['away'],
                    current_game['home'],
                    home_court_bonuses=home_court_bonuses,
                    total_multiplier=multiplier
                )
                
                edge = calculate_edge(predicted, current_game['sportsbook_total'])
                
                actual_total = current_game['total_pts']
                predicted_over = predicted > current_game['sportsbook_total']
                actual_over = actual_total > current_game['sportsbook_total']
                
                if edge != 0:
                    result = "WIN" if (predicted_over == actual_over) else "LOSS"
                else:
                    result = "PUSH"
                
                results.append({"result": result, "edge": edge})
            except:
                continue
        
        if results:
            wins = sum(1 for r in results if r["result"] == "WIN")
            total_bets = sum(1 for r in results if r["result"] != "PUSH")
            win_rate = wins / total_bets if total_bets > 0 else 0
            avg_edge = sum(abs(r["edge"]) for r in results) / len(results)
            
            results_summary.append({
                "multiplier": multiplier,
                "games": len(results),
                "wins": wins,
                "total_bets": total_bets,
                "win_rate": win_rate,
                "avg_edge": avg_edge
            })
    
    return pd.DataFrame(results_summary)


def backtest_optimized(best_multiplier=1.05):
    """
    Run full backtest with optimized parameters.
    """
    all_games = get_historical_games(30)
    all_games = all_games.sort_values('date').reset_index(drop=True)
    
    results = []
    
    for idx in range(len(all_games)):
        current_game = all_games.iloc[idx]
        training_data = all_games.iloc[:idx]
        
        if len(training_data) < 4:
            continue
        
        try:
            model_data = calculate_team_totals(training_data, recency_weight=True)
            
            if current_game['away'] not in model_data.index or current_game['home'] not in model_data.index:
                continue
            
            # Use team-specific home court bonuses
            home_court_bonuses = calculate_home_court_advantage(model_data)
            
            predicted = predict_total_optimized(
                model_data,
                current_game['away'],
                current_game['home'],
                home_court_bonuses=home_court_bonuses,
                total_multiplier=best_multiplier
            )
            
            edge = calculate_edge(predicted, current_game['sportsbook_total'])
            actual_total = current_game['total_pts']
            predicted_over = predicted > current_game['sportsbook_total']
            actual_over = actual_total > current_game['sportsbook_total']
            
            if edge != 0:
                result = "WIN" if (predicted_over == actual_over) else "LOSS"
            else:
                result = "PUSH"
            
            results.append({
                "date": current_game['date'],
                "home": current_game['home'],
                "away": current_game['away'],
                "actual_total": actual_total,
                "sportsbook_total": current_game['sportsbook_total'],
                "predicted_total": predicted,
                "edge": edge,
                "bet": "OVER" if predicted_over else "UNDER",
                "result": result,
            })
        except:
            continue
    
    return pd.DataFrame(results)


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("GRID SEARCH: Testing parameter combinations")
    print("=" * 60)
    
    grid_results = grid_search_backtest()
    print(grid_results.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("OPTIMIZED BACKTEST: Full results with best parameters")
    print("=" * 60)
    
    optimized_results = backtest_optimized()
    print("\nDetailed Results:")
    print(optimized_results.to_string(index=False))
    
    summarize_backtest(optimized_results)
