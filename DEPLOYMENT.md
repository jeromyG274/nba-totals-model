# NBA Totals Model - Deployment Guide

## Quick Start

### Local Testing
```bash
# Install dependencies
pip install -r requirements.txt

# Run predictions once (for testing)
python schedule_predictions.py once

# Run live scheduler (runs daily at 10 AM)
python schedule_predictions.py
```

### Production Deployment

#### Option 1: Systemd Service (Linux/Ubuntu)
```bash
# Copy service file to systemd
sudo cp nba-predictions.service /etc/systemd/system/

# Enable and start
sudo systemctl enable nba-predictions.service
sudo systemctl start nba-predictions.service

# Check status
sudo systemctl status nba-predictions.service

# View logs
sudo journalctl -u nba-predictions.service -f
```

#### Option 2: Cron Job
```bash
# Edit crontab
crontab -e

# Add this line to run daily at 10 AM:
0 10 * * * cd /path/to/nba-totals-model && /usr/bin/python3 schedule_predictions.py once
```

#### Option 3: Docker
```bash
# Build image
docker build -t nba-totals-model .

# Run container
docker run -d --name nba-predictor nba-totals-model
```

## Features

- **Automatic daily predictions** - Runs at 10 AM each day
- **Real-time game data** - Fetches live scores from NBA API
- **Efficiency metrics** - Uses home/away offensive/defensive ratings
- **Home court advantage** - Adds 3.5 pt bonus for home teams
- **Betting edge calculation** - Compares predictions to sportsbook lines
- **Logging** - All predictions saved to `predictions.log`

## Configuration

Edit `schedule_predictions.py` to customize:
- **Prediction time**: Change `"10:00"` in `schedule.every().day.at()` 
- **Home court bonus**: Modify `home_court_bonus` parameter in `predict_total()`
- **Default sportsbook line**: Update `sportsbook = 220.0` (or fetch from API)

## Monitoring

Check predictions daily:
```bash
tail -f predictions.log
```

Monitor live:
```bash
python schedule_predictions.py once
```

## Troubleshooting

**No games found?**
- Check if it's NBA season (Oct-Jun)
- NBA API may be down - verify: `curl https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json`

**Predictions not running?**
- Check systemd status: `sudo systemctl status nba-predictions.service`
- Check logs: `sudo journalctl -u nba-predictions.service -n 50`
- Verify cron: `crontab -l`

**Teams not found in model?**
- Need at least 4 historical games to build model
- If first day of season, use mock data or pre-load historical games

## Performance

Recent backtest (v2 with home court bonus):
- **Win rate**: Pending re-test with home court factor
- **Avg edge**: ~6.81 points (before home court bonus)
- **Games tested**: 26
