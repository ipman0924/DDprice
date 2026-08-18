# DDprice

Excel-like browser for the Dicker Data reseller price & stock feed.

- ~102k SKUs, filter and sort on every column, CSV export of the current filter
- Data refreshed daily at 00:00 Sydney time by a GitHub Actions workflow
- Hosted on [Streamlit Community Cloud](https://streamlit.io/cloud), free tier

See `docs/adr/README.md` for the design decisions and `docs/glossary.md` for term definitions.

## Repo layout

```
app.py                          Streamlit app
refresh.py                      Feed download + validate + write data/feed.parquet
requirements.txt                Runtime deps for the app AND the workflow
.streamlit/config.toml          Streamlit theme + server config
.github/workflows/refresh.yml   Daily cron in GitHub Actions
data/feed.parquet               Committed by the workflow (not in initial repo)
data/meta.json                  Committed by the workflow (not in initial repo)
docs/                           ADRs and glossary
```

## Local setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Seed the data folder once locally so the app has something to render:

```bash
export DD_DOWNLOAD_URL='https://portal.dickerdata.com.au/Download?file=...'
python refresh.py
```

Run the app:

```bash
streamlit run app.py
```

## Deployment

### One-time GitHub setup

1. Push this repo to a **public** GitHub repo.
2. Repo settings → Secrets and variables → Actions → **New repository secret**:
   - Name: `DD_DOWNLOAD_URL`
   - Value: your DD portal download URL (with the account-scoped token in the query string)
3. Actions tab → **Refresh DD feed** → **Run workflow** to trigger the first refresh manually. Verify a new commit lands with `data/feed.parquet` and `data/meta.json`.

### Streamlit Cloud

1. Sign in at [share.streamlit.io](https://share.streamlit.io) with your GitHub account.
2. New app → point at this repo, branch `main`, main file `app.py`.
3. Deploy. First cold start takes ~30 seconds.

If the DD download URL/token ever changes, update the GitHub Actions secret — no code change needed.

### App password

The app prompts for a password before showing data (see ADR-0015). This is UX-only — the parquet file itself is public in the repo.

- **Default password:** `jands` (hardcoded in `app.py`).
- **To rotate:** Streamlit Cloud → app Settings → Secrets → add `APP_PASSWORD = "new-password"`. No code change needed.

## How the refresh works

- Runs at **00:00 Sydney time** via two UTC cron entries (14:00 UTC for AEST, 13:00 UTC for AEDT). A time-gate step skips whichever one fires outside the intended window.
- Downloads the CSV with up to **3 attempts, 5 minutes apart** (respects DD's 10/hour rate limit).
- Validates header, row count (≥ 50k), and non-blank StockCodes before writing.
- Writes `data/feed.parquet` (Snappy-compressed, ~2–4 MB) and `data/meta.json` (refresh timestamp, row count, source SHA-256).
- Commits and pushes. Streamlit Cloud auto-redeploys.
- On any failure, the workflow fails loud, GitHub emails the owner, and the repo keeps yesterday's data.

Trigger a manual refresh any time via **Actions → Refresh DD feed → Run workflow**.

## Data quirks worth knowing

- `StockAvailable = 999999999` means **unlimited** (services, training, software licenses). Displayed as-is per ADR-0007 so the column stays numerically sortable.
- All prices are **ex-GST**.
- `TertiaryCategory` is truncated to ~20 chars by DD upstream.
- `BundledItem1..5` are dropped by `refresh.py` before writing the parquet (ADR-0014). The DD feed still ships them; we just don't surface them.

## License

Internal tool — no license specified.
