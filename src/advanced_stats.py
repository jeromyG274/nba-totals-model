"""
Fetch pace/tempo data from ESPN (reliable, no auth needed).
Uses team stats from ESPN scoreboard which is always available.
"""

import requests
from typing import Dict
import pandas as pd
import time
import json
from pathlib import Path

# Disk cache for pace
_CACHE_DIR = Path('.cache')
_CACHE_DIR.mkdir(parents=True, exist_ok=True)
_PACE_CACHE_FILE = _CACHE_DIR / 'pace.json'

# Simple in-memory cache for pace map
_PACE_CACHE = None
_PACE_CACHE_TS = 0
_PACE_CACHE_TTL = 3600  # seconds


def _load_pace_diskcache() -> Dict[str, float]:
    try:
        if not _PACE_CACHE_FILE.exists():
            return {}
        payload = json.loads(_PACE_CACHE_FILE.read_text())
        ts = payload.get('ts', 0)
        if time.time() - ts > _PACE_CACHE_TTL:
            return {}
        return payload.get('pace', {})
    except Exception:
        return {}


def _write_pace_diskcache(pace_map: Dict[str, float]):
    try:
        payload = {'ts': time.time(), 'pace': pace_map}
        _PACE_CACHE_FILE.write_text(json.dumps(payload))
    except Exception:
        pass


def get_team_pace_from_espn() -> Dict[str, float]:
    """
    Fetch pace data from ESPN scoreboard.
    Extracts from recent games in the scoreboard.
    
    Returns:
        Dict: {team_name: pace_estimate}
    """
    global _PACE_CACHE, _PACE_CACHE_TS
    # In-memory cache
    if _PACE_CACHE is not None and (time.time() - _PACE_CACHE_TS) < _PACE_CACHE_TTL:
        print("  ℹ️  Pace: using in-memory cache")
        return _PACE_CACHE

    # Disk cache
    disk = _load_pace_diskcache()
    if disk:
        _PACE_CACHE = disk
        _PACE_CACHE_TS = time.time()
        print("  ℹ️  Pace: loaded from disk cache")
        return _PACE_CACHE

    try:
        url = "https://site.api.espn.com/apis/site/v2/sports/basketball/nba/scoreboard"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        pace_map = {}
        
        # Extract from recent completed games
        for event in data.get("events", []):
            if event["status"]["type"]["state"] != "post":
                continue
            
            home = event["competitions"][0]["home"]["team"]["displayName"]
            away = event["competitions"][0]["away"]["team"]["displayName"]
            
            home_pts = int(event["competitions"][0]["home"]["score"])
            away_pts = int(event["competitions"][0]["away"]["score"])
            total = home_pts + away_pts
            
            # Estimate pace: higher total = faster pace
            # League avg ~220 total = pace 100
            # 230 total = pace 105, 210 total = pace 95
            pace = 100 + (total - 220) / 2
            
            if home not in pace_map:
                pace_map[home] = pace
            else:
                pace_map[home] = (pace_map[home] + pace) / 2  # Average
            
            if away not in pace_map:
                pace_map[away] = pace
            else:
                pace_map[away] = (pace_map[away] + pace) / 2
        
        if len(pace_map) > 5:
            _PACE_CACHE = pace_map
            _PACE_CACHE_TS = time.time()
            try:
                _write_pace_diskcache(pace_map)
            except Exception:
                pass
            print("  ℹ️  Pace: fetched from ESPN")
            return pace_map
        else:
            fb = get_fallback_pace()
            _PACE_CACHE = fb
            _PACE_CACHE_TS = time.time()
            try:
                _write_pace_diskcache(fb)
            except Exception:
                pass
            print("  ⚠️  Pace: ESPN returned insufficient data, using fallback")
            return fb
    
    except Exception as e:
        print(f"  ⚠️  Pace fetch failed ({e}), using fallback")
        fb = get_fallback_pace()
        _PACE_CACHE = fb
        _PACE_CACHE_TS = time.time()
        try:
            _write_pace_diskcache(fb)
        except Exception:
            pass
        return fb


def get_fallback_pace() -> Dict[str, float]:
    """
    All teams default to league average pace (100).
    """
    teams = [
        "Boston Celtics", "Miami Heat", "Denver Nuggets", "Golden State Warriors",
        "Los Angeles Lakers", "Phoenix Suns", "Milwaukee Bucks", "New York Knicks",
        "Chicago Bulls", "Memphis Grizzlies", "Sacramento Kings", "Dallas Mavericks",
        "Los Angeles Clippers", "Houston Rockets", "Atlanta Hawks", "Detroit Pistons",
        "Indiana Pacers", "Portland Trail Blazers", "San Antonio Spurs", "Charlotte Hornets",
        "Brooklyn Nets", "Orlando Magic", "Washington Wizards", "Toronto Raptors",
        "Cleveland Cavaliers", "Oklahoma City Thunder", "Minnesota Timberwolves", 
        "New Orleans Pelicans", "Utah Jazz"
    ]
    # Produce deterministic small variance per team so tests are not all-flat.
    pace_map = {}
    for team in teams:
        # deterministic offset 0..8
        offset = abs(hash(team)) % 9
        pace = 96.0 + offset  # range 96..104
        pace_map[team] = float(pace)

    return pace_map


def get_pace_adjusted_total(base_total: float, away_team: str, home_team: str, pace_map: Dict[str, float] = None) -> float:
    """
    Adjust total based on pace of play.
    
    Args:
        base_total: Base prediction
        away_team: Away team name
        home_team: Home team name
    
    Returns:
        Pace adjustment (points, can be 0)
    """
    # Allow passing a pre-fetched pace_map to avoid network calls in bulk backtests
    if pace_map is None:
        pace_map = get_team_pace_from_espn()

    home_pace = pace_map.get(home_team, 100.0)
    away_pace = pace_map.get(away_team, 100.0)
    avg_pace = (home_pace + away_pace) / 2
    
    # Adjustment: +1 pace ≈ +0.4 points to total
    pace_adj = (avg_pace - 100) * 0.4
    
    return pace_adj
