# Architecture Decision Records

One file per load-bearing decision. Numbered chronologically.

Status values: `Proposed` → `Accepted` → (`Superseded by ADR-NNNN` | `Deprecated`).

## Index

- [ADR-0001](0001-primary-user-and-scope.md) — Primary user is internal staff doing bulk browse/export. **Accepted.**
- [ADR-0002](0002-source-feed-characteristics.md) — Source feed is the Dicker Data authenticated CSV endpoint. **Accepted.**
- [ADR-0003](0003-refresh-strategy.md) — Truncate-and-load with backup-swap. **Superseded by ADR-0009.**
- [ADR-0004](0004-failure-handling.md) — Bounded retry, preserve last-good, alert. **Accepted** (with alerting updated to GitHub Actions email).
- [ADR-0005](0005-dealer-price-protection.md) — `DealerEx` protected by shared-password gate. **Superseded by ADR-0008.**
- [ADR-0006](0006-grid-model-and-default-filter.md) — Server-paginated grid with `Vendor="Shure"` default filter. **Accepted.**
- [ADR-0007](0007-sentinel-display.md) — Display `StockAvailable=999999999` as the literal value. **Accepted.**
- [ADR-0008](0008-dealer-price-exposure-accepted.md) — `DealerEx` is displayed publicly. **Accepted** (owner's classification).
- [ADR-0009](0009-refresh-via-github-actions.md) — Daily refresh runs in GitHub Actions. **Accepted.**
- [ADR-0010](0010-stack-streamlit-pandas-aggrid.md) — Streamlit + pandas + streamlit-aggrid. **Accepted.**
- [ADR-0011](0011-hosting-streamlit-cloud-public-repo.md) — Streamlit Community Cloud + public GitHub repo. **Accepted.**
- [ADR-0012](0012-data-format-in-repo.md) — Data stored as Parquet in the repo. **Accepted.**
- ADR-0013 — Bundle (parent/child) modeling. **No longer relevant** — columns dropped per ADR-0014.
- [ADR-0014](0014-drop-bundle-and-margin-columns.md) — Drop `BundledItem1..5` and margin columns from the deployed schema. **Accepted.**
