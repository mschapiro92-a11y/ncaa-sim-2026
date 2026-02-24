import os
import requests
from supabase import create_client
from datetime import datetime

# Setup
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

def auto_update():
    # 1. Pull current NCAA Basketball Scoreboard from ESPN
    api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
    
    try:
        data = requests.get(api_url).json()
    except Exception as e:
        print(f"API Error: {e}")
        return

    events = data.get('events', [])
    print(f"Found {len(events)} games on ESPN.")

    for event in events:
        comp = event.get('competitions', [{}])[0]
        teams = comp.get('competitors', [])
        if len(teams) < 2: continue

        # Get ESPN IDs and Names
        # Team 0 is usually Home, Team 1 is Away
        t1 = teams[0].get('team', {})
        t2 = teams[1].get('team', {})
        
        id1, name1 = t1.get('id'), t1.get('shortDisplayName')
        id2, name2 = t2.get('id'), t2.get('shortDisplayName')

        # Get Date/Time and convert to Day of Week
        raw_date = event.get('date', '') 
        day_label = "Upcoming"
        if raw_date:
            dt = datetime.strptime(raw_date, '%Y-%m-%dT%H:%MZ')
            day_label = dt.strftime('%A')

        # 2. ENSURE TEAMS EXIST: Upsert teams so we don't get Foreign Key errors
        supabase.table("teams").upsert([
            {"id": id1, "name": name1},
            {"id": id2, "name": name2}
        ]).execute()

        # 3. UPSERT MATCHUP: Add or update the game
        # We use a custom ID (e.g., "123-456") to prevent duplicates
        matchup_id = f"{min(id1, id2)}-{max(id1, id2)}"
        
        status = event.get('status', {}).get('type', {}).get('state')
        winner_id = None
        if status == "post": # Game is finished
            for t in teams:
                if t.get('winner') == True:
                    winner_id = t.get('team', {}).get('id')

        print(f"Syncing: {name1} vs {name2} on {day_label}")
        supabase.table("matchups").upsert({
            "id": matchup_id,
            "team_1_id": id1,
            "team_2_id": id2,
            "day": day_label,
            "game_date": raw_date[:10],
            "winner_id": winner_id
        }).execute()

if __name__ == "__main__":
    auto_update()
