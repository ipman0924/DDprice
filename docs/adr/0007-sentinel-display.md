# ADR-0007: Display StockAvailable=999999999 as the literal value

Status: Accepted
Date: 2026-08-18

## Context

DD encodes "unlimited stock" (training courses, software licenses, services) as `StockAvailable = 999999999`. Options considered:

- Render as `"Unlimited"` or `∞`.
- Render as `"N/A — Service"`.
- Render blank.
- Show the raw number.

## Decision

**Show the raw number.** The owner's reasoning: consistent numeric type in the column makes filtering and sorting predictable — mixing strings and numbers in one column breaks numeric range filters.

Small UI accommodations:

- Right-align the column.
- Column header tooltip: "`999999999` denotes unlimited stock (services / training / software licenses)."
- The `StockAvailable` filter panel includes a **preset**: "Unlimited (999999999)" as one of the quick-filter chips (see [ADR-0006](0006-grid-model-and-default-filter.md)).

## Consequences

- **First-time users will need to see the tooltip once.** The consistency benefit for regular users outweighs the one-time learning cost.
- **No translation logic in the query or template path** — the value flows through untouched. Fewer bugs.
- **Later reversal is cheap.** If the owner changes their mind, we add a display transform in one template partial without schema changes.
