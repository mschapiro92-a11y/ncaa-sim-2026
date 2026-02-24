import os
import requests
from supabase import create_client
from datetime import datetime

# Setup
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

def find_team_id(name):
    """Searches your 'teams' table to find the ID for an NCAA name"""
    if not name: return None
    # Use 'ilike' for a fuzzy match (e.g., 'Duke' matches 'Duke Blue Devils')
    res = supabase.table("teams").select("id").ilike("name", f"%{name}%").execute()
    return res.data[0]['id'] if res.data else None

def auto_update():
    # 1. Get NCAA Schedule (The best source for dates)
    api_url = "https://ncaa-api.henrygd.me/scoreboard/basketball-men/d1"
    try:
        data = requests.get(api_url).json()
    except:
        print("API Error")
        return

    games = data.get('games', [])
    print(f"Found {len(games)} games to check.")

    for game in games:
        # Get names from NCAA
        ncaa_home = game.get('home', {}).get('names', {}).get('short', '')
        ncaa_away = game.get('away', {}).get('names', {}).get('short', '')

        # Find the IDs in your Supabase 'teams' table
        home_id = find_team_id(ncaa_home)
        away_id = find_team_id(ncaa_away)

        if home_id and away_id:
            # Get the day of the week
            raw_date = game.get('startDate', '')
            day_label = datetime.strptime(raw_date, '%Y-%m-%d').strftime('%A') if raw_date else "TBD"

            print(f"Match: {ncaa_home} vs {ncaa_away} -> Updating to {day_label}")
            
            # UPDATE: Find the matchup where these two IDs play each other
            supabase.table("matchups").update({
                "day": day_label,
                "game_date": raw_date
            }).eq("team_1_id", home_id).eq("team_2_id", away_id).execute()
        else:
            print(f"Skipping: Couldn't map {ncaa_home} or {ncaa_away}")

if __name__ == "__main__":
    auto_update()
