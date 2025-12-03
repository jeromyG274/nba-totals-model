def calculate_team_totals(df):
    """
    Simple model:
    Offensive efficiency = average points scored
    Defensive efficiency = average points allowed
    """
    df_home = df.groupby("home").agg(
        avg_scored_home=("home_pts", "mean"),
        avg_allowed_home=("away_pts", "mean")
    )

    df_away = df.groupby("away").agg(
        avg_scored_away=("away_pts", "mean"),
        avg_allowed_away=("home_pts", "mean")
    )

    df_combined = df_home.join(df_away, how="outer").fillna(0)
    return df_combined
