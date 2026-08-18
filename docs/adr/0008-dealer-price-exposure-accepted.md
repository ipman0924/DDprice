# ADR-0008: DealerEx is displayed publicly — owner has classified it as non-confidential

Status: Accepted
Date: 2026-08-18
Supersedes: [ADR-0005](0005-dealer-price-protection.md)

## Context

Earlier in the design process (ADR-0005) I raised that the Dicker Data reseller agreement typically treats dealer cost (`DealerEx`) as confidential, and recommended a shared-password gate to protect it. On reviewing the Streamlit + public GitHub deployment (see [ADR-0011](0011-hosting-streamlit-cloud-public-repo.md)), the gate would be trivially defeated by anyone reading the committed data file — the whole model collapses.

The owner's stated position:

> "DealerEx is not really confidential as it's public knowledge in the market."

The owner is closer to the AU IT distribution market than I am, and this call is theirs to make.

## Decision

`DealerEx` is displayed on the public app alongside `RRPEx`. No authentication, no shared-password gate, no `/internal` route.

## Consequences

- **Architecture simplifies.** No auth code, no session management, no dual-route split, no `DDPRICE_INTERNAL_PASSWORD` secret.
- **Compatible with public-repo Streamlit deployment.** The data file with `DealerEx` can be committed openly.
- **Residual risk is the owner's.** If Dicker Data later objects, the mitigation is: (a) drop `DealerEx` from the deployed data (one-line ingest change) and (b) purge git history if requested. Recovery path is fast.
- **This ADR is the authoritative record** that the exposure was intentional and reasoned, not an oversight. Do not re-raise the concern in future design work on this project unless DD's stance is known to have changed.

## Rejected: continue with the gate

Rejected on architectural grounds — the gate cannot work on a public GitHub repo since the raw data is fetchable independently of the app.

## Rejected: drop DealerEx from the deployed data

Rejected because the owner values the DealerEx column for the internal browse workflow (margin comparison, cost-check during quotes).
