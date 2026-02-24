cat << 'EOF' > updater.py
import os
import sys
import requests
from supabase import create_client
from datetime import datetime

def print_now(text):
    print(text, flush=True)

print_now(">>> STARTING MAIN REPO ROBOT <<<")

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

def auto_update():
    # Simulation dates: yesterday through the weekend
    api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=50&limit=500&dates=20260223-20260301"
    
    try:
        data = requests.get(api_url).json()
        events = data.get('events', [])
        print_now(f"🔍 Found {len(events)} games.")

        for event in events:
            comp = event.get('competitions', [{}])[0]
            teams = comp.get('competitors', [])
            t1, t2 = teams[0].get('team', {}), teams[1].get('team', {})
            id1, id2 = t1.get('id'), t2.get('id')
            
            # AUTO-PLUMBING: Adds teams to Supabase if they aren't there
            supabase.table("teams").upsert([
                {"id": id1, "name": t1.get('shortDisplayName')},
                {"id": id2, "name": t2.get('shortDisplayName')}
            ]).execute()

            m_id = f"{min(str(id1), str(id2))}-{max(str(id1), str(id2))}"
            print_now(f"✅ Syncing: {t1.get('shortDisplayName')} vs {t2.get('shortDisplayName')}")
            
            supabase.table("matchups").upsert({
                "id": m_id,
                "team_1_id": id1,
                "team_2_id": id2,
                "day": datetime.strptime(event.get('date'), '%Y-%m-%dT%H:%MZ').strftime('%A'),
                "game_date": event.get('date')[:10]
            }).execute()
    except Exception as e:
        print_now(f"❌ ERROR: {e}")

if __name__ == "__main__":
    auto_update()
    print_now(">>> TASK COMPLETE <<<")
EOF
