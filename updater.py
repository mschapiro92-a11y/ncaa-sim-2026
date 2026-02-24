import os
import requests
from supabase import create_client
from datetime import datetime

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

def auto_update():
    api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard"
    data = requests.get(api_url).json()

    for event in data.get('events', []):
        comp = event.get('competitions', [{}])[0]
        teams = comp.get('competitors', [])
        
        # Extract ESPN info
        t1_data = teams[0].get('team', {})
        t2_data = teams[1].get('team', {})
        
        id1, name1 = t1_data.get('id'), t1_data.get('shortDisplayName')
        id2, name2 = t2_data.get('id'), t2_data.get('shortDisplayName')

        # AUTO-PLUMBING: If the team doesn't exist, add it now
        supabase.table("teams").upsert([
            {"id": id1, "name": name1},
            {"id": id2, "name": name2}
        ]).execute()

        # Get Date and Status
        raw_date = event.get('date', '')
        day_label = datetime.strptime(raw_date, '%Y-%m-%dT%H:%MZ').strftime('%A')
        
        # Check for winner
        winner_id = None
        if event.get('status', {}).get('type', {}).get('state') == "post":
            for t in teams:
                if t.get('winner') == True:
                    winner_id = t.get('team', {}).get('id')

        # Upsert the matchup
        m_id = f"{min(id1, id2)}-{max(id1, id2)}"
        print(f"Syncing: {name1} vs {name2} ({day_label})")
        
        supabase.table("matchups").upsert({
            "id": m_id,
            "team_1_id": id1,
            "team_2_id": id2,
            "day": day_label,
            "game_date": raw_date[:10],
            "winner_id": winner_id
        }).execute()

if __name__ == "__main__":
    auto_update()
