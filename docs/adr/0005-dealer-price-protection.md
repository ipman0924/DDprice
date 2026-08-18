# ADR-0005: DealerEx protected by shared-password gate

Status: **Superseded by [ADR-0008](0008-dealer-price-exposure-accepted.md)**
Date: 2026-08-18

## Context

The DD feed contains two prices per SKU:

- **`RRPEx`** — Recommended Retail Price. Public information.
- **`DealerEx`** — our confidential cost from DD.

Publishing `DealerEx` openly is a breach of the DD reseller agreement and exposes our margin structure to competitors and customers.

The owner has confirmed the app is otherwise public (no per-user accounts) but accepts a **shared-password gate** to protect DealerEx views.

## Decision

Two routes:

- `/` (public) — full catalog, all columns **except** `DealerEx`. RRP shown as-is.
- `/internal` (gated) — full catalog, all columns **including** `DealerEx`.

Gate implementation:

- Single shared password, read from environment variable `DDPRICE_INTERNAL_PASSWORD`.
- Compared with constant-time comparison (`hmac.compare_digest` or equivalent).
- On success, set a signed session cookie (`internal=1`, HttpOnly, Secure in production, SameSite=Lax).
- Session lasts 30 days unless the server-side session secret rotates.
- Failed logins are rate-limited (e.g. 5 attempts per IP per hour) to slow brute force.

**Do not:**

- Commit the password to source.
- Log the password or include it in error messages.
- Send `DealerEx` in any JSON payload served under `/` — protect at the query layer, not the template layer, to prevent accidental leakage via API responses.

## Consequences

- **No user accounts to manage.** Adds ~30 lines of auth code.
- **Password strength is the owner's responsibility.** The current chosen password is short and lowercase; owner accepts the tradeoff (soft-gate on a low-severity page). Rotate via env var if it leaks.
- **DealerEx never leaves the server for anonymous sessions.** The `/` route's DB queries do not select the column.
- **Compliance posture is defensible.** We can point to the gate if DD ever audits — this is a good-faith measure to keep dealer cost confidential.

## Rejected: no gate at all

Rejected. Publishing `DealerEx` openly is a business risk we cannot accept even if the owner is willing.

## Rejected: full auth system with per-user accounts

Rejected. Over-engineered for the size of the audience.
