# Glossary

Terms in this project. Column names use the exact casing from the Dicker Data feed.

## Domain terms

- **SKU** — Stock Keeping Unit. A single sellable line item. In this feed the SKU is `StockCode`.
- **Dicker Data (DD)** — Australian IT distributor. Source of the daily price/stock feed.
- **Reseller / Dealer** — us (the account holder). Buys from DD at `DealerEx`, resells at or near `RRPEx`.
- **Feed** — the CSV published by DD. Full snapshot, refreshed by DD on their schedule (we pull daily at ~midnight AEST/AEDT).
- **RRP (Recommended Retail Price)** — the price DD suggests we resell at. `RRPEx` is ex-GST.
- **Dealer price** — our cost from DD. `DealerEx` is ex-GST.
- **Ex-GST / Inc-GST** — Australian goods and services tax. All price columns in the feed are ex-GST. Any inc-GST display in the UI is a computed field (× 1.1).
- **Stock on hand (SOH)** — physical inventory DD holds. In the feed: `StockAvailable`.
- **Unlimited-stock sentinel** — the literal value `999999999` in `StockAvailable`, used for non-physical items (training, software licenses, services). Must be translated in UI — never displayed as a number.
- **ETA** — expected time of arrival for backordered items. Blank when in stock.
- **Bundle / Kit** — a StockCode whose contents are other StockCodes. Referenced via `BundledItem1..5`.

## Feed columns (as shipped)

| Column | Meaning | Notes |
|---|---|---|
| `StockCode` | DD's internal SKU | Primary key candidate. Leading zeros preserved as string. |
| `Vendor` | Manufacturer / brand | E.g. LUMIFY, CISCO, HP. |
| `VendorStockCode` | Manufacturer's part number | Often equals `StockCode` but not always. |
| `StockDescription` | Human-readable name | Free text, quoted when contains commas. |
| `PrimaryCategory` | Top-level category | E.g. SOFTWARE, HARDWARE. |
| `SecondaryCategory` | Mid-level category | E.g. TRAINING. |
| `TertiaryCategory` | Leaf category | **Truncated by DD to ~20 chars.** |
| `RRPEx` | Recommended retail, ex-GST | String-formatted decimal. |
| `DealerEx` | Our cost, ex-GST | String-formatted decimal. |
| `StockAvailable` | Units on hand | See sentinel note above. |
| `ETA` | Expected arrival date | Blank when in stock or N/A. |
| `Status` | Item lifecycle | Observed: `A` = Active. Others TBC. |
| `Type` | Item classification | Observed: `StockedItem`. Others TBC. |
| `BundledItem1..5` | Child SKUs (StockCodes) | Blank for non-bundles. |

## Operational terms

- **Refresh window** — the nightly job that pulls a fresh feed and swaps it into the live table.
- **Last-good snapshot** — the most recent `data/feed.parquet` committed to `main`. Kept live if the next refresh fails.
- **Rate limit** — DD portal enforces 10 downloads/hour and ~50/day. Retry policy must respect this (see ADR-0004).
- **Refresh workflow** — GitHub Actions job at `.github/workflows/refresh.yml` that pulls the DD CSV and commits a new `data/feed.parquet`. Runs daily at 00:00 Australia/Sydney (ADR-0009).
- **Cold start** — the ~10–20s delay when the first user each week visits the Streamlit app after it has been sleeping. Not a bug; a Streamlit Cloud free-tier characteristic.
