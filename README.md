# Strava training dashboard

A self-updating dashboard: a GitHub Actions job pulls fresh Strava data on a
schedule and commits `data.json`; the static `index.html` page reads that
file at load time. GitHub Pages serves the page for free.

## One-time setup

1. **Create this repo on GitHub** and push these files (`index.html`,
   `data.json`, `scripts/fetch_strava.py`,
   `.github/workflows/update-dashboard.yml`).

2. **Register a Strava API app**: strava.com/settings/api
   - Authorization Callback Domain: `localhost`
   - Note the Client ID and Client Secret.

3. **Get a refresh token** (one time):
   ```
   https://www.strava.com/oauth/authorize?client_id=YOUR_CLIENT_ID&redirect_uri=http://localhost&response_type=code&scope=activity:read_all
   ```
   Approve, copy the `code=` value from the redirected (broken) localhost
   URL, then:
   ```bash
   curl -X POST https://www.strava.com/oauth/token \
     -d client_id=YOUR_CLIENT_ID \
     -d client_secret=YOUR_CLIENT_SECRET \
     -d code=THE_CODE \
     -d grant_type=authorization_code
   ```
   Save the `refresh_token` from the response.

4. **Add repo secrets**: Settings → Secrets and variables → Actions → New
   repository secret. Add all three:
   - `STRAVA_CLIENT_ID`
   - `STRAVA_CLIENT_SECRET`
   - `STRAVA_REFRESH_TOKEN`

5. **Enable GitHub Pages**: Settings → Pages → Source: Deploy from a branch
   → Branch: `main`, folder: `/ (root)`.

6. **Run the workflow once manually** to confirm it works: Actions tab →
   "Update Strava dashboard data" → Run workflow. Check that `data.json`
   gets updated and committed.

Your dashboard will be live at `https://yourusername.github.io/reponame`
and will refresh automatically every day (the schedule in the workflow
runs at 13:00 UTC — edit the cron line to change that).

## Files

- `index.html` — the dashboard page. Fetches `data.json` on load.
- `data.json` — generated data. Committed by the workflow; a seed copy is
  included so the page works before the first automated run.
- `scripts/fetch_strava.py` — refreshes the Strava token, pulls the last
  20 weeks of activities, computes the aggregates the dashboard needs.
- `.github/workflows/update-dashboard.yml` — runs the script daily and
  commits the result.
