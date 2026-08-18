# ADR-0011: Hosted on Streamlit Community Cloud from a public GitHub repo

Status: Accepted
Date: 2026-08-18

## Context

Owner's preference is **GitHub + Streamlit**. The free tier of Streamlit Community Cloud requires a public GitHub repo. Given [ADR-0008](0008-dealer-price-exposure-accepted.md) treats `DealerEx` as non-confidential, the public-repo constraint no longer blocks anything.

## Decision

- Repo is **public** on GitHub.
- App deploys from `main` branch on Streamlit Community Cloud (free tier).
- Secrets (the DD download URL / token) live in **Streamlit Cloud's Secrets manager** for the app, and in **GitHub Actions Secrets** for the refresh workflow. Never in source.
- No auth on the app — public URL.

## Consequences

- **US$0/month** for hosting.
- **10–20 second cold start** for the first visitor after ~a week of inactivity. Considered acceptable for an internal browse tool.
- **1 GB RAM / 1 CPU cap** on the app — fits our workload comfortably.
- **Public URL is shareable** with anyone who needs it. If usage patterns later require gated access, revisit ADR-0008 and consider the Streamlit Teams paid tier.
- **Streamlit Cloud auto-redeploys** on every push to `main`, including the daily refresh commit from GitHub Actions.

## Open items

- The exact Streamlit Cloud URL depends on the GitHub repo name and Streamlit account. Deferred until the repo is created.
