# ADR-0015: Soft-password gate on the app (UX only, not security)

Status: Accepted
Date: 2026-08-18

## Context

The owner asked for a login form on the app: the user enters a password (`jands`) before seeing any data. This partially reverses [ADR-0011](0011-hosting-streamlit-cloud-public-repo.md), which had "no auth on the app — public URL" as the stated posture.

## Decision

Add a password prompt to `app.py`. Behavior:

- On first load, show a form with a single password field.
- Correct password → set `st.session_state["authed"] = True` and re-render the app.
- Wrong password → show an error and re-prompt.
- Password is compared with `hmac.compare_digest` for constant-time equality.

Password source, in order of precedence:

1. `st.secrets["APP_PASSWORD"]` if present (recommended for rotation via Streamlit Cloud dashboard).
2. Fallback default: the literal string `"jands"` in `app.py`.

## Consequences

- **This is a UX gate, not a security control.** The data file `data/feed.parquet` is committed to a public GitHub repo (ADR-0011) and can be downloaded without ever visiting the app. Anyone who wants the data can bypass the gate entirely. The gate exists to make the tool feel private and stop random visitors who land on the URL from seeing content immediately.
- **The default password is visible in the source.** Because the repo is public (ADR-0011), the literal `"jands"` string is publicly readable. Anyone who reads `app.py` sees it. Rotation via `st.secrets` doesn't fix this for the default value; it only helps if the deployed override differs from the source default.
- **Session persistence:** authentication is per browser tab / Streamlit session. Users re-authenticate when they open a new tab or after the app sleeps and cold-starts.
- **[ADR-0011](0011-hosting-streamlit-cloud-public-repo.md)** is partially amended — the "public URL, no auth" posture is now "public URL, soft gate."
- **[ADR-0008](0008-dealer-price-exposure-accepted.md)** still stands — `DealerEx` is classified non-confidential by the owner. This ADR does not re-open the confidentiality question; the gate is not motivated by data sensitivity.

## Rotation

To change the password without a code change:

1. Streamlit Cloud → your app → Settings → Secrets.
2. Add: `APP_PASSWORD = "new-password"`.
3. Save. The app rehydrates within a few seconds.
