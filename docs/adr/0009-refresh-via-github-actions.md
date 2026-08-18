# ADR-0009: Daily refresh runs in GitHub Actions and commits data to the repo

Status: Accepted
Date: 2026-08-18
Supersedes: [ADR-0003](0003-refresh-strategy.md)

## Context

Streamlit Community Cloud apps have no persistent server process — they only run when a user visits. Cron cannot live in the app itself. We need an external scheduler that:

- Runs once a day at 00:00 Australia/Sydney.
- Fetches the DD CSV using an auth token that must stay secret.
- Validates the file before publishing (per [ADR-0004](0004-failure-handling.md)).
- Makes the resulting data available to the Streamlit app on next cold start.

## Decision

Use **GitHub Actions** as the scheduler. A workflow at `.github/workflows/refresh.yml` runs on `schedule`, downloads the CSV, validates it, and commits the result back to the repo. The Streamlit app reads the committed file at startup, cached via `@st.cache_data`.

### Schedule handling for Australian DST

Australia/Sydney observes daylight saving. Cron in GitHub Actions runs in UTC. The workflow uses **two schedule entries**, one for AEST (UTC+10) and one for AEDT (UTC+11):

```yaml
on:
  schedule:
    - cron: '0 14 * * *'  # 00:00 AEST (UTC+10) — winter
    - cron: '0 13 * * *'  # 00:00 AEDT (UTC+11) — summer
```

The workflow's first step checks the current Sydney time and exits early if it's not within the intended window, so we don't refresh twice near DST transitions.

### Workflow steps

1. Checkout the repo.
2. Read `DD_DOWNLOAD_URL` from GitHub Actions Secrets.
3. Download the CSV to `/tmp/feed.csv` — retry per [ADR-0004](0004-failure-handling.md) (3 attempts, 5-minute spacing).
4. Validate:
   - HTTP 200, non-empty, not the rate-limit JSON error.
   - Header row matches expected 18 columns.
   - Row count ≥ 50,000.
   - No blank `StockCode`.
5. Parse CSV → normalized form (see [ADR-0012](0012-data-format-in-repo.md) for format).
6. Write to `data/feed.csv` (or `data/feed.parquet` — see ADR-0012) with `refreshed_at` timestamp in a sibling `data/meta.json`.
7. `git add data/ && git commit -m "chore: refresh feed {date}" && git push`.
8. On any failure: workflow fails loud — GitHub emails the owner and shows a red X in the Actions tab. Repo still has yesterday's data committed, so the Streamlit app keeps serving it.

### What the Streamlit app sees

The app reads `data/feed.*` at cold start via `@st.cache_data`. When GitHub Actions pushes a new commit, Streamlit Cloud auto-redeploys and the cache invalidates on next startup. There is a small "Last refreshed: {timestamp}" indicator in the footer, read from `data/meta.json`.

## Consequences

- **Free.** GitHub Actions free-tier minutes cover a daily 2-minute job easily.
- **Full audit trail** — every refresh is a commit; the git log is the refresh history.
- **Failure model is intuitive** — a failed workflow leaves the previous commit as the live data, exactly matching "keep serving yesterday's data on failure."
- **No cron-on-server complexity** — no VPS to keep alive, no systemd timer to debug.
- **DD token lives in GitHub Actions Secrets**, never in source. Rotation is a one-click UI change.
- **Repo grows by ~19 MB/day of history** in raw CSV. Mitigation options: use Parquet (much smaller), commit to a data-only orphan branch, or use Git LFS. Decided in [ADR-0012](0012-data-format-in-repo.md).
- **Streamlit auto-redeploy on push** means users hitting the app mid-morning may see the new data appear a few seconds into their session. Acceptable.
