from src.data_fetch import get_games
from src.process import calculate_team_totals
from src.model import predict_total
from src.edge import calculate_edge

# 1. Fetch game data for today
df = get_games()

print(f"Found {len(df)} games today")
print(df)
print()

if len(df) == 0:
    print("No games found. Exiting.")
    exit(0)

# Filter for completed games (non-zero scores)
df_completed = df[df['total_pts'] > 0]

if len(df_completed) == 0:
    print("No completed games found yet.")
    print("\nToday's matchups:")
    for idx, row in df.iterrows():
        print(f"  {row['away']} @ {row['home']}")
    exit(0)

print(f"{len(df_completed)} completed games:")
print(df_completed)
print()

# 2. Build team efficiency dataset
model_data = calculate_team_totals(df_completed)

# 3. Pick first two teams to demo
home_team = df_completed.iloc[0]['home']
away_team = df_completed.iloc[0]['away']

predicted_total = predict_total(model_data, away_team, home_team)

# 4. Compare to sportsbook number
sportsbook_total = 236.5
edge = calculate_edge(predicted_total, sportsbook_total)

# 5. Print results
print("=" * 50)
print(f"Matchup: {away_team} @ {home_team}")
print("=" * 50)
print("Predicted Total:", predicted_total)
print("Sportsbook Total:", sportsbook_total)
print("Edge:", edge)
