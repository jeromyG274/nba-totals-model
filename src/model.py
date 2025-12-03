def predict_total(model_data, away_team, home_team):
    """
    Predict NBA total:
    avg_scored + avg_allowed from both teams
    """
    home = model_data.loc[home_team]
    away = model_data.loc[away_team]

    pred = (
        home["avg_scored_home"] +
        away["avg_scored_away"] +
        home["avg_allowed_home"] +
        away["avg_allowed_away"]
    ) / 2

    return round(pred, 1)
