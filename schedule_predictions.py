#!/usr/bin/env python3
"""
Scheduled daily NBA totals predictions.
Run this with: python schedule_predictions.py
Or set up as cron: 0 10 * * * cd /path/to/nba-totals-model && python schedule_predictions.py
"""

import schedule
import time
import logging
from datetime import datetime
from src.data_fetch import get_games
from src.process import calculate_team_totals
from src.model import predict_total
from src.edge import calculate_edge
from src.odds_fetch import get_nba_games_with_odds
from src.injury import adjust_prediction_for_injuries
from src.advanced_stats import get_pace_adjusted_total
from src.streaks import calculate_streak_adjustment
from src.line_movement import should_filter_based_on_movement

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('predictions.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def run_predictions():
    """
    Fetch today's games and generate predictions using live sportsbook odds.
    """
    logger.info("=" * 60)
    logger.info("Starting daily predictions")
    logger.info("=" * 60)
    
    try:
        # Fetch games
        df = get_games()
        logger.info(f"Found {len(df)} games today")
        
        if len(df) == 0:
            logger.info("No games found.")
            return
        
        # Fetch live sportsbook odds
        logger.info("Fetching live sportsbook odds from The Odds API...")
        odds_games = get_nba_games_with_odds(sportsbook="draftkings")
        
        # Build odds lookup
        odds_map = {}
        for game in odds_games:
            key = (game["away"].lower(), game["home"].lower())
            odds_map[key] = game["total"]
        logger.info(f"Retrieved odds for {len(odds_map)} games")
        
        # Filter for completed games (non-zero scores)
        df_completed = df[df['total_pts'] > 0]
        
        if len(df_completed) == 0:
            logger.info("No completed games yet.")
            logger.info("\nToday's matchups:")
            for idx, row in df.iterrows():
                logger.info(f"  {row['away']} @ {row['home']}")
            return
        
        logger.info(f"{len(df_completed)} completed games found")
        
        # Build model
        model_data = calculate_team_totals(df_completed)
        
        # Generate predictions
        predictions = []
        for idx, row in df_completed.iterrows():
            try:
                away = row['away']
                home = row['home']
                
                # Get live sportsbook line
                key = (away.lower(), home.lower())
                sportsbook = odds_map.get(key, 220.0)
                
                # Base prediction
                predicted = predict_total(model_data, away, home)
                logger.info(f"\n{away} @ {home}:")
                logger.info(f"  Base: {predicted}")
                
                # Apply enhancements
                # 1. Advanced stats (pace adjustment)
                pace_adj = get_pace_adjusted_total(predicted, away, home)
                if pace_adj != 0:
                    predicted += pace_adj
                    logger.info(f"  Pace: {pace_adj:+.1f} → {predicted}")
                
                # 2. Injury adjustment
                injury_adj = adjust_prediction_for_injuries(away, home)
                if injury_adj != 0:
                    predicted += injury_adj
                    logger.info(f"  Injury: {injury_adj:+.1f} → {predicted}")
                
                # 3. Streak adjustment
                streak_adj = calculate_streak_adjustment(home, away)
                if streak_adj != 0:
                    predicted += streak_adj
                    logger.info(f"  Streak: {streak_adj:+.1f} → {predicted}")
                
                # Calculate edge
                edge = calculate_edge(predicted, sportsbook)
                
                # 4. Line movement filter
                should_bet = should_filter_based_on_movement(predicted, sportsbook, "OVER" if edge > 0 else "UNDER")
                
                bet = "OVER" if edge > 0 else "UNDER" if edge < 0 else "PASS"
                if not should_bet:
                    bet = "FILTERED"
                
                prediction = {
                    "home": home,
                    "away": away,
                    "predicted": predicted,
                    "sportsbook": sportsbook,
                    "edge": edge,
                    "bet": bet
                }
                predictions.append(prediction)
                
                logger.info(
                    f"  Final: Pred {predicted:.1f} vs Book {sportsbook} | "
                    f"Edge: {edge:+.1f} ({bet})"
                )
            except Exception as e:
                logger.error(f"Error predicting {home} vs {away}: {e}")
                continue
        
        # Summary
        logger.info("-" * 60)
        logger.info(f"Generated {len(predictions)} predictions")
        
        return predictions
        
    except Exception as e:
        logger.error(f"Error in run_predictions: {e}", exc_info=True)


def schedule_daily():
    """
    Schedule predictions to run daily at 10 AM.
    """
    logger.info("Scheduler started")
    schedule.every().day.at("10:00").do(run_predictions)
    
    while True:
        schedule.run_pending()
        time.sleep(60)


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "once":
        # Run once (for testing or manual execution)
        run_predictions()
    else:
        # Run as scheduler
        schedule_daily()
