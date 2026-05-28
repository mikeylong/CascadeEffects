# Hyatt Tea Dance Walkway Occupancy Historical Accuracy Review

Date: 2026-05-16

Gate: source-art candidate review

Status: `review_ready_pending_episode_package_keep`

## Measurement Target

This pass measures ImageGen output against both Hyatt Regency atrium architecture and the tea dance event texture.

## Canonical Visual Facts

- Multi-story hotel atrium with stacked balcony/room openings.
- Suspended walkways/skywalks crossing the atrium volume.
- Visible hanger rods descending to the walkway structure.
- Plausible box-beam/load-path relationship.
- Public event floor below the walkways.
- Tea dance party details: balloons, tables, dancing couples, and crowd density.
- Anonymous people visible on the suspended walkways and/or balcony rails above the atrium.
- Pre-collapse condition only.

## Candidate Reads

| Candidate | Historical accuracy | Hyatt atrium architecture | Tea dance specificity | Walkway occupancy | Notes |
| --- | --- | --- | --- | --- | --- |
| `variant_f_tea_dance_walkway_spectators` | `pass` | `pass` | `pass` | `pass` | Strong combined read: event floor, balloons, walkways, hanger rods, and people on walkways. Right rail is usable. |
| `variant_g_party_floor_occupied_walkways` | `pass` | `pass` | `pass` | `pass` | Strongest event/balloon/dancing read; architecture is still credible, though the right rail area is busier than F. |
| `variant_h_balanced_tea_dance_load_path` | `pass` | `pass` | `pass` | `pass` | Best balanced candidate for party specificity plus a broad atrium/load-path read; right rail area has usable dark glass. |

## Gate Effect

All three candidates are reviewable. Human review should choose one keeper or request a targeted tighten pass. No motion readiness, rough proof, final render, publish readiness, or upload is authorized by this review alone.
