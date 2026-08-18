# ADR-0014: Drop BundledItem1..5 and margin columns from the deployed schema

Status: Accepted
Date: 2026-08-18

## Context

The DD feed ships 18 columns. The initial deployment kept all of them and added two derived columns (`Margin`, `MarginPct`). After using the app briefly, the owner has said:

- `BundledItem1..5` (columns N–R in the CSV) are not useful for the browse workflow.
- `Margin` and `MarginPct` are not useful either.

## Decision

`refresh.py` drops the following columns from the DataFrame before writing `data/feed.parquet`:

- `BundledItem1`, `BundledItem2`, `BundledItem3`, `BundledItem4`, `BundledItem5`
- `Margin`, `MarginPct` (no longer computed at all)

The **validation step still checks against the full DD-shipped 18-column header** — this is deliberate. If DD ever restructures the CSV, we want to hear about it in the workflow log, not silently keep working with an unexpected shape.

## Consequences

- **App shows 13 columns instead of 20.** Cleaner grid, cleaner Excel export.
- **[ADR-0006](0006-grid-model-and-default-filter.md)** — the bundle-column filter guidance in that ADR is no longer relevant. Left in the ADR as historical context; the current grid config in `app.py` doesn't reference those columns.
- **[ADR-0013](README.md)** — bundle modeling is now not just deferred but explicitly not needed. If bundles ever matter, we'd revisit both this ADR and 0013.
- **Parquet size:** ~3.94 MB (down from ~4.40 MB with margin columns).
- **No breakage to the ingestion contract with DD** — we still fetch the same URL and expect the same 18-column header.

## Superseded by / supersedes

Not a supersession of any prior ADR — a pure schema trim.
