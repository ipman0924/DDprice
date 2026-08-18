# ADR-0004: Failure handling — bounded retry, preserve last-good, alert

Status: Accepted
Date: 2026-08-18

## Context

The DD portal enforces **10 requests/hour and ~50/day** per account. The nightly refresh has essentially one shot; a naive retry loop can burn the daily budget and lock us out for 24 hours. The owner has asked for: keep serving yesterday's data on failure, and alert.

## Decision

**Retry policy for the download step:**

- Up to **3 attempts** total.
- Wait **≥ 5 minutes** between attempts (respects the 10/hour limit with headroom).
- Escalate to alert only after all 3 fail.

**Validation gate (before commit):**

The downloaded file must pass these checks before the truncate+load runs:

- HTTP 200 and non-empty body.
- Body is not the rate-limit JSON error (`"API calls quota exceeded"`).
- Header row starts with `StockCode,Vendor,`.
- Row count ≥ 50,000 (guards against a truncated download).
- No `StockCode` is blank on any parsed row.

Any failed check aborts the run without touching the live table.

**On any abort or crash:**

- Under [ADR-0009](0009-refresh-via-github-actions.md), the workflow fails before committing new data. The repo still holds yesterday's `data/feed.parquet`, so the Streamlit app continues serving it.
- GitHub emails the workflow owner automatically on failure, and the Actions tab shows a red X. That is the alert channel; no separate SMTP setup needed.
- Failure logs (which check failed, HTTP status, row count observed) live in the workflow run — one click from the email.

## Consequences

- **Rate-limit safe.** 3 retries × 5-minute spacing = well under 10/hour.
- **User-visible outcome on failure:** app keeps serving yesterday's snapshot. The only signal to the user is a small "last refreshed: {timestamp}" indicator in the footer.
- **Alerting requires a channel.** Simplest v1: SMTP env vars → owner's email. Deferred: Slack, PagerDuty, etc.
- **We consciously do not fail loud** (no maintenance page). Serving day-old prices is materially better than serving nothing for an internal browse tool.
