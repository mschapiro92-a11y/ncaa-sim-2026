import os
import requests
from supabase import create_client
from datetime import datetime

# Setup
URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
supabase = create_client(URL, KEY)

def auto_update():
    # Adding 'groups=50' to get ALL D1 games, not just Top 25
    api_url = "https://site.api.espn.com/apis/site/v2/sports/basketball/mens-college-basketball/scoreboard?groups=50&limit=500"
    
    try:
        response = requests.get(api_url)
        data = response.json()
    except Exception as e:
        print(f"❌ API Call Failed: {e}")
        return

    events = data.get('events', [])
    print(f"🔍 ESPN API found {len(events)} total games today.")

    if not events:
        print("⚠️ No games found in the API response. Check if games have tipped off yet.")
        return

    for event in events:
        comp = event.get('competitions', [{}])[0]
        teams = comp.get('competitors', [])
        
        # Team Data
        t1 = teams[0].get('team', {})
        t2 = teams[1].get('team', {})
        id1, name1 = t1.get('id'), t1.get('shortDisplayName')
        id2, name2 = t2.get('id'), t2.get('shortDisplayName')

        # 1. Auto-Add Teams (The "Auto-Plumbing")
        supabase.table("teams").upsert([
            {"id": id1, "name": name1},
            {"id": id2, "name": name2}
        ]).execute()

        # 2. Date/Time Logic
        raw_date = event.get('date', '')
        day_label = "Upcoming"
        if raw_date:
            dt = datetime.strptime(raw_date, '%Y-%m-%dT%H:%MZ')
            day_label = dt.strftime('%A')

        # 3. Score/Winner Logic
        winner_id = None
        status = event.get('status', {}).get('type', {}).get('state')
        if status == "post":
            for t in teams:
                if t.get('winner') == True:
                    winner_id = t.get('team', {}).get('id')

        # 4. Upsert Matchup
        m_id = f"{min(str(id1), str(id2))}-{max(str(id1), str(id2))}"
        
        print(f"✅ Syncing Matchup: {name1} vs {name2} on {day_label}")
        
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
