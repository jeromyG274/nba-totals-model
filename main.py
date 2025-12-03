from src.data_fetch import get_games
from src.process import calculate_team_totals
from src.model import predict_total
from src.edge import calculate_edge

# 1. Fetch game data for a date (pick any date during NBA season)
df = get_games("2024-01-15")

# 2. Build team efficiency dataset
model_data = calculate_team_totals(df)

# 3. Predict a total for a matchup
away = "Los Angeles Lakers"
home = "Golden State Warriors"

predicted_total = predict_total(model_data, away, home)

# 4. Compare to sportsbook number
sportsbook_total = 236.5
edge = calculate_edge(predicted_total, sportsbook_total)

# 5. Print results
print("Predicted Total:", predicted_total)
print("Sportsbook Total:", sportsbook_total)
print("Edge:", edge)
