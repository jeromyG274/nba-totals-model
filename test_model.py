"""
Mock test for the NBA totals model using sample data.
"""
import pandas as pd
from src.process import calculate_team_totals
from src.model import predict_total
from src.edge import calculate_edge

# Mock game data
mock_games = pd.DataFrame([
    {"date": "2024-01-15", "home": "Golden State Warriors", "away": "Los Angeles Lakers", 
     "home_pts": 120, "away_pts": 115, "total_pts": 235},
    {"date": "2024-01-16", "home": "Golden State Warriors", "away": "Boston Celtics", 
     "home_pts": 110, "away_pts": 118, "total_pts": 228},
    {"date": "2024-01-17", "home": "Los Angeles Lakers", "away": "Denver Nuggets", 
     "home_pts": 108, "away_pts": 125, "total_pts": 233},
])

print("Mock Games Data:")
print(mock_games)
print()

# 2. Build team efficiency dataset
model_data = calculate_team_totals(mock_games)
print("Team Efficiency Metrics:")
print(model_data)
print()

# 3. Predict a total for a matchup
away = "Los Angeles Lakers"
home = "Golden State Warriors"

predicted_total = predict_total(model_data, away, home)

# 4. Compare to sportsbook number
sportsbook_total = 236.5
edge = calculate_edge(predicted_total, sportsbook_total)

# 5. Print results
print("=" * 50)
print(f"Matchup: {away} @ {home}")
print("=" * 50)
print(f"Predicted Total: {predicted_total}")
print(f"Sportsbook Total: {sportsbook_total}")
print(f"Edge: {edge}")
print(f"Recommendation: {'OVER' if edge > 0 else 'UNDER'} (edge of {abs(edge)} points)")
