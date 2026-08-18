# ADR-0002: Source feed is the Dicker Data authenticated CSV endpoint

Status: Accepted
Date: 2026-08-18

## Context

The single source of truth for prices and stock is a CSV feed published by Dicker Data, accessed via an authenticated URL on the DD reseller portal. We need to pin down what the feed actually looks like before designing schema and pipeline.

## Decision

The source is the DD `DickerDataDataFeedCSV.csv` endpoint. Observed characteristics as of 2026-08-18:

| Property | Value |
|---|---|
| Format | CSV, ex-GST prices, header row present |
| Encoding | ASCII, no BOM |
| Delimiter | comma, quoted strings for text with commas |
| File size | ~19 MB |
| Row count | ~101,891 data rows |
| Columns | 18 (see [glossary](../glossary.md)) |
| Auth | opaque token embedded in URL query string |
| Origin | Cloudflare, served from Sydney (`cf-ray: ...-SYD`) |
| Rate limit | **10 requests/hour, ~50/day** per account |

## Consequences

**Security.** The download URL contains what appears to be an account-scoped auth token. It must:
- Live in a secret/env var, never in source or logs.
- Be treated as rotatable — the pipeline must accept the URL as configuration.
- Be kept out of any error message we surface to end users.

**Rate limit shapes retry policy.** With only 10 attempts per hour, the pipeline gets essentially one shot per refresh window. Retry policy: at most 3 attempts spaced ≥5 minutes apart, then alert and preserve last-good snapshot.

**Size fits SQLite.** At ~19 MB / ~102k rows, the whole dataset loads into memory or SQLite in seconds. No streaming ingest needed. Simple architectures are fine.

**Data quirks that ingestion must handle:**

- `StockAvailable = 999999999` is a sentinel for "unlimited" (training/software). Store as-is; translate at the UI layer.
- `TertiaryCategory` is truncated to ~20 chars by DD. Downstream mapping may be needed if it's used for display.
- `BundledItem1..5` are foreign references to other `StockCode` values within the same file. Bundle modeling is deferred to a separate ADR.
- All prices are ex-GST as strings (`"5500.00"`). Parse to decimal on ingest.

**Open questions.**

- What's DD's own publish schedule? If they update the CSV once every 24h and we poll at midnight AEST, we're aligned. If they update in-day, we may want to reconsider.
- Does the token rotate? On what cadence? Where does it come from in the portal?
- What does `Status` other than `A` mean? What `Type` values exist besides `StockedItem`?
