# ADR-0010: Stack is Streamlit + pandas + streamlit-aggrid

Status: Accepted
Date: 2026-08-18

## Context

Owner chose **Streamlit + GitHub** as the platform. The stack decisions inside that constraint are:

- Data manipulation: pandas vs polars vs SQLite.
- Grid component: `st.dataframe` (built-in) vs `streamlit-aggrid` (community wrapper for AG Grid) vs `streamlit-data-editor`.
- Language & version.

## Decision

- **Python 3.11+** (compatible with Streamlit Community Cloud runtime).
- **Streamlit** for the app shell.
- **pandas** for data loading, filter, and CSV export. At ~102k rows / 18 columns the DataFrame is ~30 MB in memory — comfortably inside the 1 GB app limit.
- **streamlit-aggrid** for the Excel-like grid. Delivers per-column filter/sort/pagination (per [ADR-0006](0006-grid-model-and-default-filter.md)), CSV export button, and column resize/reorder. AG Grid Community is free and open-source.
- **Data cached with `@st.cache_data`** keyed on the file's mtime or hash so the DataFrame loads once per app boot, not per user session.

### Not chosen and why

- **`st.dataframe` built-in.** Its filter/sort is fine but not "Excel-like" enough for this use case. Rejected.
- **polars.** Faster than pandas at this size but adds an unfamiliar API for future contributors. Overkill at 19 MB. Rejected.
- **SQLite.** Adds a query layer for no clear benefit at this data size. All operations users perform (filter, sort, contains-search, export) are one-line pandas calls. Rejected.

## Consequences

- **Single `requirements.txt`** — streamlit, pandas, streamlit-aggrid. No build tooling, no bundler, no TypeScript.
- **App structure is one `app.py`** — Streamlit apps are just Python scripts. Splitting into modules is optional.
- **First cold start is fast** — pandas reads the CSV once, caches, done. On Streamlit Cloud that's a few seconds.
- **`st.cache_data` invalidation** — cache key must include the file's modification time (or content hash) so a new refresh commit triggers a reload, not a stale-cache hit.
