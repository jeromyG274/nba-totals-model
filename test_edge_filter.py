#!/usr/bin/env python3
"""
Filter predictions by edge threshold.
Only bet when edge is strong (> 2pts) to avoid noise.
"""

import pandas as pd
from src.backtest import backtest_model, summarize_backtest


def filter_by_edge(results_df, min_edge=2.0):
    """
    Filter predictions to only those with sufficient edge.
    
    Args:
        results_df: DataFrame from backtest_model()
        min_edge: Minimum absolute edge to consider (default 2.0pts)
    
    Returns:
        Filtered DataFrame
    """
    filtered = results_df[results_df['edge'].abs() >= min_edge].copy()
    return filtered


if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("EDGE FILTERING ANALYSIS")
    print("=" * 60)
    
    # Run backtest
    results = backtest_model()
    
    if len(results) == 0:
        print("No results")
        exit(1)
    
    # Test different edge thresholds
    for threshold in [0.0, 2.0, 3.0, 5.0]:
        filtered = filter_by_edge(results, threshold)
        
        if len(filtered) == 0:
            print(f"\nEdge > {threshold}pts: No bets")
            continue
        
        wins = (filtered['result'] == 'WIN').sum()
        total = len(filtered)
        win_rate = wins / total
        avg_edge = filtered['edge'].abs().mean()
        
        print(f"\nEdge > {threshold}pts: {total} bets")
        print(f"  Win Rate: {wins}/{total} = {win_rate:.1%}")
        print(f"  Avg Edge: {avg_edge:.2f} pts")
        print(f"  Bets Eliminated: {len(results) - total}")
