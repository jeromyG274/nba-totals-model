# NBA Totals Model - AI Coding Instructions

## Architecture Overview

This is a **sports betting analytics pipeline** that predicts NBA game totals by analyzing team efficiency metrics and comparing predictions to sportsbook odds.

**Data Flow:**
1. `data_fetch.py` → Fetches real-time game data from free NBA official API
2. `process.py` → Aggregates data into team offensive/defensive efficiency metrics
3. `model.py` → Predicts game total using efficiency averaging formula
4. `edge.py` → Calculates betting edge (predicted vs. sportsbook line)
5. `backtest.py` → Validates model against historical games

**Core Logic:** The model predicts game totals by averaging:
- Home team offensive efficiency (avg_scored_home) + Away team defensive efficiency (avg_allowed_away)
- Away team offensive efficiency (avg_scored_away) + Home team defensive efficiency (avg_allowed_home)

## Key Files & Patterns

- **`main.py`**: Real-time workflow - fetches today's games, shows matchups, predicts when games complete
- **`src/data_fetch.py`**: Pulls live games from NBA API using free scoreboard/boxscore endpoints (no auth required)
- **`src/process.py`**: Creates team-indexed DataFrame with `_home`/`_away` suffixed columns
- **`src/backtest.py`**: Historical validation - runs predictions on past games with accumulated training data
- **Data contracts**: All functions use full team names (e.g., "Los Angeles Lakers"), pandas DataFrames with strict column names

## Development Workflow

**Running live predictions:**
```bash
python main.py  # Fetches today's games, predicts when complete
```

**Backtesting:**
```bash
python backtest.py  # Tests model on historical data, shows win rate & edge
```

**External API:** Uses free NBA endpoints:
- `https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json` (live games)
- `https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{gameId}.json` (advanced stats: pace, ORtg, DRtg)

## Common Patterns & Conventions

- **Efficiency metrics**: Separate home/away splits (teams perform ~3-5 pts better at home)
- **League average baseline**: Default to 110 points per team when historical data missing
- **Missing data handling**: Use `.fillna(0)` in process.py, fallback to league avg in model.py
- **Rounding**: Predictions (1 decimal), edges (2 decimals)
- **Edge interpretation**: Positive edge = model predicts higher (bet OVER), negative = bet UNDER
- **Backtest training**: Use all prior games (not fixed window) to build team efficiency data

## Integration Points

- `get_games()` returns DataFrame: `[date, home, away, home_pts, away_pts, total_pts]`
- `calculate_team_totals()` accepts game DataFrame, returns team-indexed with `[avg_scored_home, avg_allowed_home, avg_scored_away, avg_allowed_away]`
- `predict_total(model_data, away_team, home_team)` requires both teams in model_data index

## Testing & Validation

**Backtest results (v2 with home court bonus: 40% win rate on 26 games):**
- Win rate improved from 30.8% → 40% with 3.5pt home bonus
- 10 wins, 15 losses, 1 push
- Avg edge: 6.96 points
- Model now more aggressive on OVER bets due to home court factor

**Production deployment:**
- Use `schedule_predictions.py once` for manual testing
- Use `schedule_predictions.py` (no args) for daemon mode (daily at 10 AM)
- See DEPLOYMENT.md for systemd/cron setup

**Known limitations:**
- No injury data, rest day adjustments, or back-to-back penalties
- Uses simple averaging (not weighted by recency)
- Sportsbook lines not calibrated for model bias
- Home court bonus is fixed (could be team-specific)
