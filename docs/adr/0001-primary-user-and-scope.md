# ADR-0001: Primary user is internal staff doing bulk browse/export

Status: Accepted
Date: 2026-08-18

## Context

The web interface can serve several audiences: internal SKU lookup (one item at a time), internal bulk browse/export (filter, sort, export subsets), or external customers browsing a catalog. Each implies a different UI, different auth model, and different scope.

## Decision

Primary user is **internal staff performing bulk browse and export**. The interface optimizes for:

- Filter/sort across the full ~102k SKUs
- Pagination (no infinite-scroll into 100k rows)
- Export a filtered subset to CSV / Excel
- Fast single-SKU lookup as a secondary path (search box)

Out of scope: external customer catalog, images, cart/quote, customer-specific pricing.

## Consequences

- Auth: single-tenant, internal login only. No public exposure of dealer prices.
- No image/rich-media pipeline needed.
- Query patterns favor **indexed filtering on category, vendor, stock status, and full-text on description**.
- Export is a first-class feature, not an afterthought — needs to handle up to ~102k rows without timing out.
