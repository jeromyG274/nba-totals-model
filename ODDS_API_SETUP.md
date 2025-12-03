# The Odds API Setup

The model now uses **live sportsbook odds** from The Odds API instead of hardcoded defaults.

## Free Tier Features
- **500 requests/month** (enough for daily predictions)
- **20+ sportsbooks** covered (DraftKings, FanDuel, BetMGM, Caesars, etc.)
- **No credit card required** for free tier
- Real-time game lines and odds

## Setup Instructions

### 1. Create Account
Go to https://theosdsapi.com and sign up for free account.

### 2. Get API Key
- Log in to https://theosdsapi.com/account
- Copy your API key

### 3. Set Environment Variable
```bash
# Add to your shell profile (~/.bashrc, ~/.zshrc, etc.)
export ODDS_API_KEY="your_api_key_here"

# Or set temporarily in terminal
export ODDS_API_KEY="your_api_key_here"
```

### 4. Verify Setup
```bash
python -c "from src.odds_fetch import get_nba_games_with_odds; games = get_nba_games_with_odds(); print(f'Got {len(games)} games with live odds')"
```

## Usage

Once API key is set:

```bash
# Run predictions with live odds
python schedule_predictions.py once

# Schedule daily at 10 AM
python schedule_predictions.py
```

## Fallback Behavior
If `ODDS_API_KEY` is not set or API fails:
- Falls back to realistic default odds (220.5 per game)
- Logs warning to console
- Predictions still work, but use generic line instead of live odds

## Supported Sportsbooks
By default uses `draftkings`. To change:

```python
from src.odds_fetch import get_nba_games_with_odds

# Get FanDuel odds
games = get_nba_games_with_odds(sportsbook="fanduel")

# Get BetMGM odds
games = get_nba_games_with_odds(sportsbook="betmgm")
```

Available: `draftkings`, `fanduel`, `betmgm`, `caesars`, `pointsbet`, `barstool`, etc.

## API Rate Limits
- Free tier: 500 requests/month
- Each prediction run uses ~1 request
- Daily scheduling (30 days) = ~30 requests/month (plenty of buffer)

## Troubleshooting

**"ODDS_API_KEY not set"**
- Set environment variable: `export ODDS_API_KEY="your_key"`
- Restart terminal after setting

**"Using fallback odds (not live)"**
- Check API key is correct
- Check network connectivity
- Monitor API usage at https://theosdsapi.com/account

**API not returning games**
- May be outside NBA season
- Check if games are scheduled for today
- API returns only upcoming/live games, not historical
