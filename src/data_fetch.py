import requests
import pandas as pd

API_URL = "https://api.balldontlie.io/v1/games"
API_KEY = ""  # Add key if required

def get_games(date):
    headers = {"Authorization": API_KEY} if API_KEY else {}

    params = {
        "dates[]": date,
        "per_page": 100
    }

    r = requests.get(API_URL, params=params, headers=headers)
    data = r.json()["data"]

    rows = []
    for g in data:
        home = g["home_team"]["full_name"]
        away = g["visitor_team"]["full_name"]
        home_pts = g["home_team_score"]
        away_pts = g["visitor_team_score"]

        rows.append({
            "date": date,
            "home": home,
            "away": away,
            "home_pts": home_pts,
            "away_pts": away_pts,
            "total_pts": home_pts + away_pts
        })

    return pd.DataFrame(rows)
