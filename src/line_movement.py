"""
Line movement filter: Simple fallback for when The Odds API unavailable.

If current line differs significantly from default: trust sportsbook calibration.
Otherwise: proceed with model prediction.
"""

from typing import Dict, Tuple


def calculate_line_movement(default_line: float, current_line: float) -> Tuple[float, str]:
    """
    Simple line movement: compare to default league average.
    
    Args:
        default_line: Default/estimated line (220.5)
        current_line: Current sportsbook line
    
    Returns:
        Tuple: (movement_pts, direction)
    """
    movement = current_line - default_line
    
    if movement > 1.0:
        return movement, "UP"  # Line moved up
    elif movement < -1.0:
        return movement, "DOWN"  # Line moved down
    else:
        return movement, "NONE"


def should_filter_based_on_movement(predicted_total: float, sportsbook_total: float, predicted_bet: str) -> bool:
    """
    Filter bets if going heavily against market (>12pts difference = suspicious).
    Conservative: only filter extreme outliers.
    
    Args:
        predicted_total: Model prediction
        sportsbook_total: Sportsbook line
        predicted_bet: "OVER" or "UNDER"
    
    Returns:
        True if should place bet, False if should skip (filter)
    """
    # Very large discrepancies = trust market, skip bet
    discrepancy = abs(predicted_total - sportsbook_total)
    
    # Only filter if difference > 12 points (extreme outlier)
    if discrepancy > 12.0:
        return False
    
    return True


def apply_line_movement_filter(prediction_data: Dict) -> Dict:
    """
    Apply line movement filter to a prediction.
    
    Args:
        prediction_data: Dict with predicted_total, sportsbook_total, bet
    
    Returns:
        Modified prediction_data with filter applied
    """
    should_bet = should_filter_based_on_movement(
        prediction_data.get('predicted_total', 220.5),
        prediction_data.get('sportsbook_total', 220.5),
        prediction_data.get('bet', 'PASS')
    )
    
    if not should_bet:
        prediction_data['bet'] = 'FILTERED'
    
    return prediction_data
