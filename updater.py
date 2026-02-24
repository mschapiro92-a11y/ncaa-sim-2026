print("!!! DEBUG START: SCRIPT IS INITIALIZING !!!")
import os
import requests
from supabase import create_client
from datetime import datetime

# Setup
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

print(f"Checking Env: URL exists: {bool(URL)}, Key exists: {bool(KEY)}")

supabase = create_client(URL, KEY)

def auto_update():
    print("Entering auto_update function...")
    # Look at a massive date range to ensure we find games
    api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=50&limit=500&dates=20260220-20260301"
    
    try:
        print(f"Fetching ESPN API: {api_url}")
        response = requests.get(api_url)
        data = response.json()
        events = data.get('events', [])
        print(f"🔍 Found {len(events)} events in the API.")
    except Exception as e:
        print(f"❌ ERROR DURING API CALL: {e}")
        return

    for event in events:
        try:
            comp = event.get('competitions', [{}])[0]
            teams = comp.get('competitors', [])
            t1_data = teams[0].get('team', {})
            t2_data = teams[1].get('team', {})
            
            id1, name1 = t1_data.get('id'), t1_data.get('shortDisplayName')
            id2, name2 = t2_data.get('id'), t2_data.get('shortDisplayName')

            # Auto-Add Teams
            supabase.table("teams").upsert([
                {"id": id1, "name": name1},
                {"id": id2, "name": name2}
            ]).execute()

            raw_date = event.get('date', '')
            day_label = datetime.strptime(raw_date, '%Y-%m-%dT%H:%MZ').strftime('%A')
            m_id = f"{min(str(id1), str(id2))}-{max(str(id1), str(id2))}"
            
            print(f"✅ Syncing: {name1} vs {name2}")
            
            supabase.table("matchups").upsert({
                "id": m_id,
                "team_1_id": id1,
                "team_2_id": id2,
                "day": day_label,
                "game_date": raw_date[:10]
            }).execute()
        except Exception as e:
            print(f"Error processing a game: {e}")
            continue

if __name__ == "__main__":
    auto_update()
    print("!!! DEBUG END: SCRIPT FINISHED !!!")
