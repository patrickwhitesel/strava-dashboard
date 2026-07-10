"""
Refreshes a Strava access token and pulls recent activities into data.json,
which the dashboard's index.html reads at load time.
 
Expects three environment variables (set as GitHub Actions secrets):
  STRAVA_CLIENT_ID
  STRAVA_CLIENT_SECRET
  STRAVA_REFRESH_TOKEN
"""
 
import os
import json
import sys
from datetime import datetime, timedelta
from collections import defaultdict
import urllib.request
import urllib.parse
 
CLIENT_ID = os.environ["STRAVA_CLIENT_ID"]
CLIENT_SECRET = os.environ["STRAVA_CLIENT_SECRET"]
REFRESH_TOKEN = os.environ["STRAVA_REFRESH_TOKEN"]
 
TOKEN_URL = "https://www.strava.com/oauth/token"
ACTIVITIES_URL = "https://www.strava.com/api/v3/athlete/activities"
 
WEEKS_OF_HISTORY = 20
 
 
def post_json(url, data):
    body = urllib.parse.urlencode(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
 
 
def get_json(url, headers):
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())
 
 
def refresh_access_token():
    resp = post_json(TOKEN_URL, {
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "grant_type": "refresh_token",
        "refresh_token": REFRESH_TOKEN,
    })
    return resp["access_token"]
 
 
def fetch_activities(access_token):
    after_ts = int((datetime.utcnow() - timedelta(weeks=WEEKS_OF_HISTORY)).timestamp())
    activities = []
    page = 1
    headers = {"Authorization": f"Bearer {access_token}"}
    while True:
        qs = urllib.parse.urlencode({"after": after_ts, "per_page": 100, "page": page})
        batch = get_json(f"{ACTIVITIES_URL}?{qs}", headers)
        if not batch:
            break
        activities.extend(batch)
        page += 1
        if len(batch) < 100:
            break
    return activities
 
 
def m_to_mi(m):
    return round(m / 1609.34, 1)
 
 
def m_to_ft(m):
    return round(m * 3.28084)
 
 
def build_dashboard_data(activities):
    total_distance_mi = round(sum(m_to_mi(a["distance"]) for a in activities), 1)
    total_elev_ft = round(sum(m_to_ft(a["total_elevation_gain"]) for a in activities))
    total_moving_hr = round(sum(a["moving_time"] for a in activities) / 3600, 1)
 
    sport_counts = defaultdict(int)
    for a in activities:
        sport_counts[a["type"]] += 1
 
    weekly = defaultdict(lambda: {"distance_mi": 0.0})
    for a in activities:
        dt = datetime.fromisoformat(a["start_date_local"].replace("Z", ""))
        week_start = dt - timedelta(days=dt.weekday())
        key = week_start.strftime("%Y-%m-%d")
        weekly[key]["distance_mi"] += m_to_mi(a["distance"])
 
    weekly_sorted = sorted(weekly.items())
    week_labels = [datetime.strptime(k, "%Y-%m-%d").strftime("%b %-d") for k, _ in weekly_sorted]
    week_distances = [round(v["distance_mi"], 1) for _, v in weekly_sorted]
 
    top_climbs = sorted(activities, key=lambda a: a["total_elevation_gain"], reverse=True)[:6]
    climbs_out = [{
        "name": a["name"],
        "date": a["start_date_local"][:10],
        "elev_ft": m_to_ft(a["total_elevation_gain"]),
        "distance_mi": m_to_mi(a["distance"]),
    } for a in top_climbs]
 
    elevation_series = [
        m_to_ft(a["total_elevation_gain"])
        for a in sorted(activities, key=lambda a: a["start_date_local"])
    ]
 
    recent_sorted = sorted(activities, key=lambda a: a["start_date_local"], reverse=True)[:10]
    recent_rides = [{
        "name": a["name"],
        "type": a["type"],
        "date": a["start_date_local"][:10],
        "distance_mi": m_to_mi(a["distance"]),
        "elev_ft": m_to_ft(a["total_elevation_gain"]),
        "moving_min": round(a["moving_time"] / 60),
    } for a in recent_sorted]
 
    return {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "total_distance_mi": total_distance_mi,
        "total_elev_ft": total_elev_ft,
        "total_moving_hr": total_moving_hr,
        "activity_count": len(activities),
        "sport_counts": dict(sport_counts),
        "week_labels": week_labels,
        "week_distances": week_distances,
        "top_climbs": climbs_out,
        "elevation_series": elevation_series,
        "recent_rides": recent_rides,
    }
 
 
def main():
    access_token = refresh_access_token()
    activities = fetch_activities(access_token)
    data = build_dashboard_data(activities)
    with open("data.json", "w") as f:
        json.dump(data, f, indent=2)
    print(f"Wrote data.json with {len(activities)} activities.")
 
 
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        print(f"Failed to update dashboard data: {e}", file=sys.stderr)
        sys.exit(1)
