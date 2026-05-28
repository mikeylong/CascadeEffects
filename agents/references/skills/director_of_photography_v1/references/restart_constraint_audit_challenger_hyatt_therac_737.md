# Restart Constraint Audit: Challenger, Hyatt, Therac, 737

## Audit Decision

For the Challenger-first production restart, all pre-existing visual constraints from Challenger, Hyatt, Therac, 737, keeper registries, casebooks, model experiments, old manifests, packaging rules, and prior render reviews are classified as `legacy_reference` by default.

No prior constraint is `active` or `conditional` until the DP imports an exact file or rule and approves it in the current episode constraint ledger.

## Classification

| source family | default status | active automatically | notes |
| --- | --- | --- | --- |
| Challenger prior visual research, v1/v2/v3, restart attempts, proof reviews, renders, manifests, Midjourney packages, diagnostic outputs | `legacy_reference` | `false` | Exact files may be imported only through the workflow scope manifest. |
| Hyatt production and visual artifacts | `legacy_reference` | `false` | May not constrain Challenger unless DP imports an exact file and ledger entry. |
| Therac production and visual artifacts | `legacy_reference` | `false` | May not constrain Challenger unless DP imports an exact file and ledger entry. |
| 737 production and visual artifacts | `legacy_reference` | `false` | May not constrain Challenger unless DP imports an exact file and ledger entry. |
| Keeper registry and casebook lessons | `legacy_reference` | `false` | Useful as candidate lessons only after exact DP import. |
| Motion backend/model experiment rules | `legacy_reference` | `false` | Backend/matrix rules require active ledger approval. |
| Caption/text/logo/UI/poster visual rules | `legacy_reference` | `false` | Final captions remain final-export owned; generated-visual controls require active ledger approval. |
| Style package hard constraints and prompt grammar | `legacy_reference` | `false` | The style skill may propose constraints, but DP ledger approval activates them. |

## Active

None.

## Conditional

None.

## Retired

None globally retired by this audit. The active episode constraint ledger may retire a specific legacy rule for the scoped short.
