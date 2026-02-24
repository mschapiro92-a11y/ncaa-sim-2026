import os
import sys
import requests
from supabase import create_client
from datetime import datetime

# FORCE LOGS TO SHOW IMMEDIATELY
def print_now(text):
    print(text, flush=True)

# Setup
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

def auto_update():
    print_now("--- STARTING ROBOT VERSION: FEB 24 ---")
    
    # We use a date range to ensure we find games to trigger the 'Auto-Plumbing'
    api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=50&limit=500&dates=20260223-20260301"
    
    try:
        print_now(f"Connecting to ESPN: {api_url}")
        data = requests.get(api_url).json()
        events = data.get('events', [])
        print_now(f"🔍 Found {len(events)} total games in the date range.")
    except Exception as e:
        print_now(f"❌ API ERROR: {e}")
        return

    for event in events:
        try:
            comp = event.get('competitions', [{}])[0]
            teams = comp.get('competitors', [])
            
            t1_data = teams[0].get('team', {})
            t2_data = teams[1].get('team', {})
            id1, name1 = t1_data.get('id'), t1_data.get('shortDisplayName')
            id2, name2 = t2_data.get('id'), t2_data.get('shortDisplayName')

            # 1. AUTO-PLUMBING: Add teams if they don't exist
            supabase.table("teams").upsert([
                {"id": id1, "name": name1},
                {"id": id2, "name": name2}
            ]).execute()

            # 2. DATE LOGIC
            raw_date = event.get('date', '')
            day_label = datetime.strptime(raw_date, '%Y-%m-%dT%H:%MZ').strftime('%A')
            
            # 3. WINNER LOGIC
            winner_id = None
            if event.get('status', {}).get('type', {}).get('state') == "post":
                for t in teams:
                    if t.get('winner') == True:
                        winner_id = t.get('team', {}).get('id')

            # 4. UPSERT MATCHUP
            m_id = f"{min(str(id1), str(id2))}-{max(str(id1), str(id2))}"
            print_now(f"✅ Syncing: {name1} vs {name2} ({day_label})")
            
            supabase.table("matchups").upsert({
                "id": m_id,
                "team_1_id": id1,
                "team_2_id": id2,
                "day": day_label,
                "game_date": raw_date[:10],
                "winner_id": winner_id
            }).execute()

        except Exception as e:
            print_now(f"⚠️ Error on game {event.get('id')}: {e}")
            continue

    print_now("--- ROBOT FINISHED SUCCESSFULLY ---")

if __name__ == "__main__":
    auto_update()
