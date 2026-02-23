import os, requests
from supabase import create_client

# Connect using your Service Key for write access
supabase = create_client(os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_ROLE_KEY"))

def auto_update():
    # Real-time NCAA D1 Scoreboard
    api_url = "https://ncaa-api.henrygd.me/scoreboard/basketball-men/d1"
    data = requests.get(api_url).json()
    
    for game in data.get('games', []):
        if game['status'] == "Final":
            # Determine the winner
            home = game['home']['team']['name']
            away = game['away']['team']['name']
            winner_name = home if int(game['home']['score']) > int(game['away']['score']) else away
            
            # Find the winner ID in our database
            team = supabase.table("teams").select("id").eq("name", winner_name).execute()
            if team.data:
                win_id = team.data[0]['id']
                # Mark the matchup as won!
                supabase.table("matchups").update({"winner_id": win_id}).or_(f"team_1_id.eq.{win_id},team_2_id.eq.{win_id}").execute()

if __name__ == "__main__": auto_update()
