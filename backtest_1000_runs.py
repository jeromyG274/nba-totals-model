#!/usr/bin/env python3
"""
1000-game equivalent backtest: Run 40 iterations of 25-game backtest 
Simulates 1000 games quickly without recomputing everything.
"""

from src.backtest import backtest_model, get_historical_games
import pandas as pd

print("=" * 80)
print("1000-GAME EQUIVALENT BACKTEST (40 × 25-game runs)")
print("=" * 80)
print("\nEach run uses realistic historical data with model enhancements.\n")

all_results = []
total_predictions = 0
total_wins = 0
total_losses = 0

for run in range(1, 41):
    print(f"Run {run:2}/40: ", end="", flush=True)
    
    try:
        # Run backtest on 25 games
        results_df = backtest_model(days_back=25, lookback_window=10)
        
        # Filter to bets only
        df_bets = results_df[results_df['filtered'] == False]
        
        wins = len(df_bets[df_bets['result'] == 'WIN'])
        losses = len(df_bets[df_bets['result'] == 'LOSS'])
        
        all_results.append(df_bets)
        total_predictions += len(df_bets)
        total_wins += wins
        total_losses += losses
        
        win_pct = 100 * wins / (wins + losses) if (wins + losses) > 0 else 0
        print(f"{wins}W-{losses}L ({win_pct:.0f}%)")
    
    except Exception as e:
        print(f"Error - {str(e)[:30]}")
        continue

# Combine all results
print("\n" + "=" * 80)
if all_results:
    combined = pd.concat(all_results, ignore_index=True)
    
    print("COMBINED 1000-GAME RESULTS (40 runs × ~25 predictions)")
    print("=" * 80)
    print(f"Total Predictions:       {total_predictions:>6}")
    print(f"Total Wins:              {total_wins:>6}")
    print(f"Total Losses:            {total_losses:>6}")
    if (total_wins + total_losses) > 0:
        win_rate = total_wins / (total_wins + total_losses)
        print(f"Overall Win Rate:        {win_rate:>6.1%}")
        print(f"Expected ROI (5% margin):{win_rate*5 - (1-win_rate)*5:>6.1f}% per bet")
    print("-" * 80)
    
    avg_edge = combined['edge'].abs().mean()
    print(f"Avg Edge Per Bet:        {avg_edge:>6.2f} points")
    
    print("\nEdge Distribution:")
    high_edge = len(combined[combined['edge'].abs() > 15])
    med_edge = len(combined[(combined['edge'].abs() > 5) & (combined['edge'].abs() <= 15)])
    low_edge = len(combined[combined['edge'].abs() <= 5])
    print(f"  High edge (>15pts):      {high_edge} ({100*high_edge/total_predictions:.1f}%)")
    print(f"  Medium edge (5-15pts):   {med_edge} ({100*med_edge/total_predictions:.1f}%)")
    print(f"  Low edge (<5pts):        {low_edge} ({100*low_edge/total_predictions:.1f}%)")
    
    overs = len(combined[combined['edge'] > 0])
    unders = len(combined[combined['edge'] < 0])
    print(f"\nOver/Under Split:")
    print(f"  OVER bets:               {overs} ({100*overs/total_predictions:.1f}%)")
    print(f"  UNDER bets:              {unders} ({100*unders/total_predictions:.1f}%)")
    
    print("=" * 80)
    combined.to_csv("backtest_1000_combined.csv", index=False)
    print("\n✓ Results saved to backtest_1000_combined.csv")
else:
    print("No results generated")
