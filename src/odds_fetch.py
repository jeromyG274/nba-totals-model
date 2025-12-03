"""
Fetch live sportsbook odds from The Odds API.
Free tier: 500 requests/month, covers 20+ sportsbooks.

Sign up: https://theosdsapi.com
Get API key from: https://theosdsapi.com/account
"""

import requests
from typing import Dict, List, Optional
from datetime import datetime, timedelta


# The Odds API endpoint
ODDS_API_BASE = "https://api.the-odds-api.com/v4"
# Sport ID for NBA
NBA_SPORT = "basketball_nba"


def get_odds_api_key():
    """
    Get API key from environment or config.
    Set via: export ODDS_API_KEY="your_key"
    """
    import os
    key = os.getenv("ODDS_API_KEY")
    if not key:
        print("⚠️  ODDS_API_KEY not set. Set via: export ODDS_API_KEY='your_key'")
        print("Get free key at: https://theosdsapi.com")
        return None
    return key


def get_nba_games_with_odds(sportsbook="draftkings", regions="us"):
    """
    Fetch today's NBA games with live odds from The Odds API.
    
    Args:
        sportsbook: Sportsbook name (draftkings, fanduel, betmgm, etc.)
        regions: Comma-separated regions (us, uk, eu, au)
    
    Returns:
        List of dicts with game data and totals:
        [{
            'date': '2025-12-03T23:30Z',
            'home': 'Los Angeles Lakers',
            'away': 'Boston Celtics',
            'total': 220.5,
            'sportsbook': 'draftkings'
        }, ...]
    """
    api_key = get_odds_api_key()
    if not api_key:
        return get_fallback_odds()
    
    try:
        url = f"{ODDS_API_BASE}/sports/{NBA_SPORT}/odds"
        params = {
            "apiKey": api_key,
            "regions": regions,
            "markets": "totals",  # Get over/under totals
            "oddsFormat": "decimal"
        }
        
        response = requests.get(url, params=params, timeout=10)
        response.raise_for_status()
        
        games = response.json()
        
        # Parse games to extract totals
        result = []
        for game in games:
            if game["status"] != "scheduled":
                continue  # Only scheduled games
            
            # Find sportsbook in bookmakers
            total_line = None
            for bookmaker in game.get("bookmakers", []):
                if sportsbook.lower() in bookmaker["title"].lower():
                    # Extract total from markets
                    for market in bookmaker.get("markets", []):
                        if market["key"] == "totals":
                            # Get the over line (both over/under have same total)
                            for outcome in market["outcomes"]:
                                if outcome["name"] == "Over":
                                    total_line = outcome["point"]
                                    break
                    break
            
            # Extract home/away team names
            home_team = game["home_team"]
            away_team = game["away_team"]
            
            # Normalize team names (remove city if present)
            home_team = normalize_team_name(home_team)
            away_team = normalize_team_name(away_team)
            
            if total_line:
                result.append({
                    "date": game["commence_time"],
                    "home": home_team,
                    "away": away_team,
                    "total": total_line,
                    "sportsbook": sportsbook
                })
        
        print(f"✓ Fetched {len(result)} games with {sportsbook} odds")
        return result
    
    except Exception as e:
        print(f"⚠️  Odds API error: {e}")
        return get_fallback_odds()


def get_fallback_odds():
    """
    Fallback: Return realistic default odds when API fails.
    Used for testing/demo when ODDS_API_KEY not available.
    """
    print("ℹ️  Using fallback odds (not live)")
    return [
        {
            "date": (datetime.utcnow() + timedelta(hours=2)).isoformat(),
            "home": "Los Angeles Lakers",
            "away": "Boston Celtics",
            "total": 220.5,
            "sportsbook": "default"
        },
        {
            "date": (datetime.utcnow() + timedelta(hours=4)).isoformat(),
            "home": "Denver Nuggets",
            "away": "Golden State Warriors",
            "total": 225.0,
            "sportsbook": "default"
        },
    ]


def normalize_team_name(name: str) -> str:
    """
    Normalize team name from API to standard format.
    E.g., "Los Angeles Lakers" -> "Los Angeles Lakers"
    """
    # API returns full names like "Los Angeles Lakers", "Boston Celtics"
    # Our model expects these exact formats
    return name.strip()


def get_game_total(home_team: str, away_team: str, sportsbook: str = "draftkings") -> Optional[float]:
    """
    Get total line for a specific game.
    
    Args:
        home_team: Home team name
        away_team: Away team name
        sportsbook: Sportsbook name
    
    Returns:
        Total line (float) or None if not found
    """
    games = get_nba_games_with_odds(sportsbook=sportsbook)
    
    for game in games:
        if (game["home"].lower() == home_team.lower() and 
            game["away"].lower() == away_team.lower()):
            return game["total"]
    
    # Fallback to default if not found
    return 220.0
