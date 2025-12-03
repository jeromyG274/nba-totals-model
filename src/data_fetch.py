import requests
import pandas as pd
from datetime import datetime, timedelta

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

SCOREBOARD_URL = "https://cdn.nba.com/static/json/liveData/scoreboard/todaysScoreboard_00.json"
BOXSCORE_URL = "https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{}.json"


def get_game_ids():
    """
    Fetch today's NBA game IDs from free NBA scoreboard.
    """
    try:
        r = requests.get(SCOREBOARD_URL, headers=HEADERS, timeout=5)
        data = r.json()
        game_ids = []
        games = data.get("scoreboard", {}).get("games", [])
        for game in games:
            game_ids.append(game["gameId"])
        return game_ids
    except:
        return []


def get_boxscore(game_id):
    """
    Pull free NBA boxscore stats for one game.
    """
    try:
        url = f"https://cdn.nba.com/static/json/liveData/boxscore/boxscore_{game_id}.json"
        r = requests.get(url, headers=HEADERS, timeout=5)
        if r.status_code == 200:
            return r.json()
    except:
        pass
    return None


def get_advanced_stats():
    """
    Returns pace, possessions, ORtg, DRtg, etc for every team playing today.
    """
    ids = get_game_ids()
    rows = []

    for gid in ids:
        box = get_boxscore(gid)
        if not box:
            continue

        try:
            home = box["game"]["homeTeam"]
            away = box["game"]["awayTeam"]

            for team in [home, away]:
                stats = team.get("statistics", {})

                rows.append({
                    "game_id": gid,
                    "team": team["teamName"],
                    "points": team["score"],
                    "pace": stats.get("pace"),
                    "possessions": stats.get("possessions"),
                    "off_rating": stats.get("offensiveRating"),
                    "def_rating": stats.get("defensiveRating"),
                    "fg_pct": stats.get("fieldGoalsPercentage"),
                    "three_pct": stats.get("threePointersPercentage"),
                })
        except Exception as e:
            continue

    return pd.DataFrame(rows)


def get_games(date=None):
    """
    Fetch NBA games with scores from today's scoreboard.
    Returns DataFrame with columns: date, home, away, home_pts, away_pts, total_pts
    """
    try:
        r = requests.get(SCOREBOARD_URL, headers=HEADERS, timeout=5)
        data = r.json()
        games = data.get("scoreboard", {}).get("games", [])
        
        rows = []
        for game in games:
            home = game["homeTeam"]["teamName"]
            away = game["awayTeam"]["teamName"]
            home_pts = game["homeTeam"]["score"]
            away_pts = game["awayTeam"]["score"]

            rows.append({
                "date": game.get("gameDate", ""),
                "home": home,
                "away": away,
                "home_pts": home_pts,
                "away_pts": away_pts,
                "total_pts": home_pts + away_pts
            })

        return pd.DataFrame(rows)
    except Exception as e:
        return pd.DataFrame()
