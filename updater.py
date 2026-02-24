import os
import requests
from supabase import create_client

# 1. Connect using your Service Key
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

def auto_update():
    # 2. Real-time NCAA D1 Scoreboard
    api_url = "https://ncaa-api.henrygd.me/scoreboard/basketball-men/d1"
    
    try:
        data = requests.get(api_url).json()
    except:
        print("API is down or unreachable.")
        return

    # 3. Process the games safely
    games = data.get('games', [])
    if not games:
        print("No games found in the API response right now.")
        return
    
    for game in games:
        # We use .get() to avoid the 'status' KeyError
        if game.get('status') == "Final":
            home = game.get('home', {}).get('team', {}).get('name')
            away = game.get('away', {}).get('team', {}).get('name')
            
            if not home or not away: continue

            # Determine winner
            h_score = int(game.get('home', {}).get('score', 0))
            a_score = int(game.get('away', {}).get('score', 0))
            winner_name = home if h_score > a_score else away
            
            # 4. Update Database
            team = supabase.table("teams").select("id").eq("name", winner_name).execute()
            if team.data:
                win_id = team.data[0]['id']
                supabase.table("matchups").update({"winner_id": win_id}).or_(f"team_1_id.eq.{win_id},team_2_id.eq.{win_id}").execute()
                print(f"Updated {winner_name} as the winner!")

if __name__ == "__main__":
    auto_update()
