import os
import requests
from supabase import create_client
from datetime import datetime

# Setup
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

def auto_update():
    # 1. Fetch ESPN Tournament Data (Replace with current year/league)
    # This URL targets the Men's NCAA Tournament scoreboard
    api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
    
    try:
        data = requests.get(api_url).json()
    except Exception as e:
        print(f"Error fetching ESPN data: {e}")
        return

    events = data.get('events', [])
    print(f"Found {len(events)} events on ESPN.")

    for event in events:
        competition = event.get('competitions', [{}])[0]
        
        # Get Team IDs (These are the ESPN IDs you already use)
        home_id = competition.get('competitors', [{}])[0].get('id')
        away_id = competition.get('competitors', [{}])[1].get('id')
        
        # Get the Date
        raw_date = event.get('date', '') # Format: 2026-03-19T16:15Z
        day_label = "Upcoming"
        
        if raw_date:
            # Parse the ESPN timestamp
            dt = datetime.strptime(raw_date, '%Y-%m-%dT%H:%MZ')
            day_label = dt.strftime('%A') # "Thursday"

        # Update Matchups in Supabase
        # We look for a matchup where these two ESPN IDs are playing
        print(f"Syncing: {day_label} game for IDs {home_id} vs {away_id}")
        
        supabase.table("matchups").update({
            "day": day_label,
            "game_date": raw_date[:10] # Just the YYYY-MM-DD part
        }).or_(f"and(team_1_id.eq.{home_id},team_2_id.eq.{away_id}),and(team_1_id.eq.{away_id},team_2_id.eq.{home_id})").execute()

if __name__ == "__main__":
    auto_update()
