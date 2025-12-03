"""
Backtest the NBA totals model on historical data.
"""
from src.backtest import backtest_model, summarize_backtest

# Run backtest with 10-game lookback window
results = backtest_model(days_back=30, lookback_window=10)

print("\nDetailed Results:")
print(results.to_string(index=False))

# Summarize
stats = summarize_backtest(results)
