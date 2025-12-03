import pandas as pd


def calculate_team_totals(df, recency_weight=True):
    """
    Calculate team efficiency metrics (offensive/defensive ratings).
    
    Args:
        df: DataFrame with columns [home, away, home_pts, away_pts]
        recency_weight: If True, weight recent games 3x more (last 30% of games)
    
    Returns:
        Team-indexed DataFrame with efficiency metrics
    """
    # Apply recency weighting
    if recency_weight and len(df) > 10:
        df = df.copy()
        # Last 30% of games get 3x weight (stronger emphasis on recent performance)
        cutoff_idx = max(0, len(df) - len(df) // 3)
        df['weight'] = 1.0
        df.loc[cutoff_idx:, 'weight'] = 3.0
    else:
        df = df.copy()
        df['weight'] = 1.0
    
    # Home team stats
    df_home = df.groupby("home").apply(
        lambda x: pd.Series({
            "avg_scored_home": (x["home_pts"] * x["weight"]).sum() / x["weight"].sum(),
            "avg_allowed_home": (x["away_pts"] * x["weight"]).sum() / x["weight"].sum()
        })
    )

    # Away team stats
    df_away = df.groupby("away").apply(
        lambda x: pd.Series({
            "avg_scored_away": (x["away_pts"] * x["weight"]).sum() / x["weight"].sum(),
            "avg_allowed_away": (x["home_pts"] * x["weight"]).sum() / x["weight"].sum()
        })
    )

    df_combined = df_home.join(df_away, how="outer").fillna(0)
    return df_combined


def calculate_home_court_advantage(df):
    """
    Calculate team-specific home court advantage from historical data.
    
    Returns dict: {team: home_advantage_points}
    """
    home_advantages = {}
    
    for team in df.index:
        if pd.isna(df.loc[team, "avg_scored_home"]) or pd.isna(df.loc[team, "avg_scored_away"]):
            home_advantages[team] = 3.5  # Default
            continue
        
        home_score = df.loc[team, "avg_scored_home"]
        away_score = df.loc[team, "avg_scored_away"]
        
        # Advantage = difference between home and away performance
        advantage = home_score - away_score
        
        # Clamp between 0-7 points (reasonable home court range)
        advantage = max(0, min(7, advantage))
        
        home_advantages[team] = advantage
    
    return home_advantages
