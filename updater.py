import os
import requests
from supabase import create_client

# 1. Connect using your Service Key for write access
# GitHub Actions provides these via the 'env' block in your YAML
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

supabase = create_client(URL, KEY)

def auto_update():
    # 2. Real-time NCAA D1 Scoreboard
    api_url = "https://ncaa-api.henrygd.me/scoreboard/basketball-men/d1"
    
    try:
        response = requests.get(api_url)
        data = response.json()
    except Exception as e:
        print(f"Error fetching data from API: {e}")
        return

    # 3. Process the games
    # We use .get('games', []) so it doesn't crash if there are no games today
    games = data.get('games', [])
    
    for game in games:
        # Check if the game is actually over
        # game.get('status') returns None instead of crashing if 'status' is missing
        if game.get('status') == "Final":
            try:
                # Extract team names and scores
                home_data = game.get('home', {})
                away_data = game.get('away', {})
                
                home_name = home_data.get('team', {}).get('name')
                away_name = away_data.get('team', {}).get('name')
                
                home_score = int(home_data.get('score', 0))
                away_score = int(away_data.get('score', 0))
                
                if not home_name or not away_name:
                    continue

                # Determine the winner
                winner_name = home_name if home_score > away_score else away_name
                print(f"Processing: {home_name} vs {away_name} -> Winner: {winner_name}")
                
                # 4. Find the winner ID in our Supabase database
                team_query = supabase.table("teams").select("id").eq("name", winner_name).execute()
                
                if team_query.data:
                    win_id = team_query.data[0]['id']
                    
                    # 5. Mark the matchup as won in the matchups table
                    # This finds the row where this team was playing and sets the winner_id
                    supabase.table("matchups") \
                        .update({"winner_id": win_id}) \
                        .or_(f"team_1_id.eq.{win_id},team_2_id.eq.{win_id}") \
                        .execute()
                    print(f"Successfully updated database for {winner_name}")
                else:
                    print(f"Warning: Team '{winner_name}' not found in database.")
                    
            except Exception as game_err:
                print(f"Error processing individual game: {game_err}")

if __name__ == "__main__":
    auto_update()
