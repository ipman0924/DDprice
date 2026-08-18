# ADR-0006: Server-paginated grid with vendor="Shure" default filter

Status: Accepted
Date: 2026-08-18

## Context

The primary use case ([ADR-0001](0001-primary-user-and-scope.md)) is Excel-like bulk browse — the owner wants filter and sort on **every** column across ~102k rows. Two grid architectures were considered:

- **Full client-side grid** — ship all rows to the browser, filter/sort in JS.
- **Server-paginated grid** — grid requests visible page from server; filters/sorts hit the DB.

## Decision

**Server-paginated grid.** All filter/sort/search operations are DB queries. The browser only holds the currently visible page (~100 rows).

**Default filter state on first paint:** `Vendor = "Shure"`. This is a visible, discoverable filter chip — not a hidden query param — so users can see it, clear it, or add other vendors.

**Filterable/sortable columns (all 18):**

Because the owner explicitly wants Excel-like behavior on every column, every column gets a filter and sort. Column-appropriate filter types:

- `Vendor`, `PrimaryCategory`, `SecondaryCategory`, `TertiaryCategory`, `Status`, `Type` — multi-select dropdowns populated from `DISTINCT` values.
- `StockCode`, `VendorStockCode`, `StockDescription`, `ETA` — text (contains / equals).
- `RRPEx`, `DealerEx` — numeric range (min/max). `DealerEx` visible only on `/internal`.
- `StockAvailable` — numeric range **plus** a quick-filter for `in stock (> 0)`, `out (= 0)`, `unlimited (= 999999999)`. Display value is left as the raw integer per [ADR-0007](0007-sentinel-display.md).
- `BundledItem1..5` — text contains; may be replaced later by a proper bundle view if [ADR-0008](0008-bundle-modeling.md) is decided.

**Indexes to add on the SQLite/Postgres table:**

- `StockCode` (unique)
- `Vendor`
- `PrimaryCategory`, `SecondaryCategory`
- `Status`
- FTS index (or LIKE with a trigram index in Postgres) on `StockDescription`

## Consequences

- **Fast initial load** — first page is a single indexed query returning ~100 rows.
- **Handles mobile / slow networks** — never ships 102k rows to a phone.
- **Requires a real backend endpoint** for the grid — typically `POST /api/rows` with `{ filters, sort, page }`. Not a static site.
- **"Select all across pages" needs care.** For export, the server accepts the current filter/sort and streams the matching rows out (see future ADR on export).

## Rejected: client-side grid

Rejected. Ships 5–10 MB JSON on first load, hurts mobile users, and breaks entirely once the feed grows. No matching benefit.
