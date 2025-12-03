"""
Get team win/loss streaks from ESPN scoreboard.
Hot teams score more, cold teams score less.
Uses fast timeout and graceful fallback.
"""

import requests
from typing import Dict


def get_team_records() -> Dict[str, Dict]:
    """
    Fetch current team records from ESPN standings.
    
    Returns:
        Dict: {team_name: {wins, losses}}
    """
    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/standings"
        response = requests.get(url, timeout=3)
        response.raise_for_status()
        data = response.json()
        
        records = {}
        
        for group in data.get("standings", []):
            for team_entry in group.get("entries", []):
                team_info = team_entry.get("team", {})
                team_name = team_info.get("displayName")
                
                if team_name:
                    stats = team_entry.get("stats", [])
                    wins = 0
                    losses = 0
                    
                    for stat in stats:
                        if stat.get("name") == "wins":
                            wins = stat.get("value", 0)
                        elif stat.get("name") == "losses":
                            losses = stat.get("value", 0)
                    
                    records[team_name] = {'wins': wins, 'losses': losses}
        
        return records if len(records) > 5 else {}
    
    except Exception:
        return {}


def calculate_streak_adjustment(home_team: str, away_team: str) -> float:
    """
    Adjust prediction based on team records (hot teams have high win %).
    
    Teams with 55%+ win rate: +1pts (hot)
    Teams with 45%- win rate: -1pts (cold)
    
    Args:
        home_team: Home team
        away_team: Away team
    
    Returns:
        Points to add to total (can be negative)
    """
    records = get_team_records()
    
    adjustment = 0.0
    
    # Home team adjustment
    if home_team in records:
        rec = records[home_team]
        total_games = rec['wins'] + rec['losses']
        if total_games > 0:
            win_pct = rec['wins'] / total_games
            if win_pct > 0.55:
                adjustment += 0.75
            elif win_pct < 0.45:
                adjustment -= 0.75
    
    # Away team adjustment
    if away_team in records:
        rec = records[away_team]
        total_games = rec['wins'] + rec['losses']
        if total_games > 0:
            win_pct = rec['wins'] / total_games
            if win_pct > 0.55:
                adjustment += 0.75
            elif win_pct < 0.45:
                adjustment -= 0.75
    
    return adjustment
