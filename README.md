# Live Orbit Data Scheduler

This public repository contains only the GitHub Actions schedules for Live
Orbit's data pipelines. The implementation remains in the private
`SamueleMarcucci/satellite-catalog-mirror` repository and is checked out with a
read-only deploy key at runtime.

## Cadence

- Satellite snapshot: every 5 minutes, staggered to minutes 02/07/12/.../57.
- TLE catalog: hourly at minute 17.
- Space-Track insights: hourly at minute 29.
- Backend health: every 5 hours.
- Full refresh: manual only.

The workflows use standard GitHub-hosted Linux runners. GitHub does not provide
repository secrets to forks, and none of these workflows run for pull requests.

## Required secrets

- `MIRROR_DEPLOY_KEY`
- `SPACE_TRACK_IDENTITY`
- `SPACE_TRACK_PASSWORD`
- `R2_ACCOUNT_ID`
- `R2_ACCESS_KEY_ID`
- `R2_SECRET_ACCESS_KEY`
- `R2_BUCKET`
- `PUBLIC_CATALOG_BASE_URL`
- `PUBLIC_SNAPSHOT_BASE_URL`

Optional pipeline integrations remain unset unless explicitly configured.
