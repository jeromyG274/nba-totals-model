from datetime import datetime, timedelta
from src.advanced_stats import get_pace_adjusted_total
from src.streaks import calculate_streak_adjustment
from src.injury import adjust_prediction_for_injuries


def is_back_to_back(game_date, recent_games, team_name):
    """
    Check if team played yesterday (back-to-back game).
    
    Args:
        game_date: Current game date (ISO format string)
        recent_games: DataFrame of recent games
        team_name: Team to check
    
    Returns:
        True if back-to-back, False otherwise
    """
    try:
        current = datetime.fromisoformat(game_date.replace('Z', '+00:00'))
        yesterday = current - timedelta(days=1)
        
        for _, game in recent_games.iterrows():
            game_dt = datetime.fromisoformat(game['date'].replace('Z', '+00:00'))
            
            # Check if team played within 24 hours
            if abs((game_dt - current).days) < 1:
                if game_dt.date() == yesterday.date():
                    if team_name in [game.get('home'), game.get('away')]:
                        return True
    except:
        pass
    
    return False
    


def predict_total(model_data, away_team, home_team, home_court_bonuses=None, total_multiplier=1.05, market_calibration=0.0, recent_games=None):
    """
    Predict NBA total with team-specific home court advantage and total scaling.
    
    Home teams typically score 3-5 pts more, so we add a bonus to the prediction.
    Total multiplier (1.05 = 5%) scales predictions higher to account for 
    higher-scoring NBA games in recent years.
    Back-to-back adjustment reduces total by 2pts if either team played yesterday.
    
    Args:
        model_data: DataFrame indexed by team with efficiency metrics
        away_team: Away team name
        home_team: Home team name
        home_court_bonuses: Dict {team: bonus_pts} for team-specific advantages (default None)
        total_multiplier: Scale factor for total (default 1.05 = +5%)
        market_calibration: Adjustment for sportsbook bias (default 0.0 = no adjustment)
        recent_games: DataFrame of recent games for B2B detection
    
    Returns:
        Predicted total (float, rounded to 1 decimal)
    """
    # League average fallback (~110 points per team per game)
    league_avg_scored = 110
    league_avg_allowed = 110
    
    try:
        home = model_data.loc[home_team]
        away = model_data.loc[away_team]
    except KeyError as e:
        raise ValueError(f"Team not found in model data: {e}")
    
    # Use fillna with league average
    home_scored = home.get("avg_scored_home", league_avg_scored) or league_avg_scored
    home_allowed = home.get("avg_allowed_home", league_avg_allowed) or league_avg_allowed
    away_scored = away.get("avg_scored_away", league_avg_scored) or league_avg_scored
    away_allowed = away.get("avg_allowed_away", league_avg_allowed) or league_avg_allowed
    
    # Base prediction
    pred = (
        home_scored +
        away_scored +
        home_allowed +
        away_allowed
    ) / 2
    
    # Add team-specific home court advantage bonus (or default 3.5pt)
    if home_court_bonuses and home_team in home_court_bonuses:
        hc_bonus = home_court_bonuses[home_team]
    else:
        hc_bonus = 3.5
    
    pred = pred + hc_bonus
    
    # Apply total multiplier
    pred = pred * total_multiplier
    
    # Apply market calibration (sportsbook bias adjustment)
    pred = pred + market_calibration
    
    # Back-to-back adjustment: teams score ~2pts less on B2B
    if recent_games is not None and len(recent_games) > 0:
        # Get game date from first column if available
        game_date = recent_games.iloc[0]['date'] if 'date' in recent_games.columns else None
        
        if game_date:
            b2b_adjustment = 0
            if is_back_to_back(game_date, recent_games, home_team):
                b2b_adjustment -= 1.0  # Home team penalty
            if is_back_to_back(game_date, recent_games, away_team):
                b2b_adjustment -= 1.0  # Away team penalty
            
            pred = pred + b2b_adjustment
    
    # Apply pace adjustment (fast teams score more)
    # advanced_stats.get_pace_adjusted_total(base_total, away_team, home_team)
    pace_adj = get_pace_adjusted_total(pred, away_team, home_team)
    pred = pred + pace_adj
    
    # Apply team streak adjustment (hot teams score more)
    streak_adj = calculate_streak_adjustment(home_team, away_team)
    if streak_adj != 0:
        print(f"Streak adjustment: {streak_adj:+.1f}pts")
    pred = pred + streak_adj

    return round(pred, 1)
