# Review Rubric

Use this rubric for every future proof packet before deciding whether to keep rendering or move on.

Then apply `judgment/promotion_workflow.md` to decide whether the result may advance to motion, reel assembly, or the keeper registry.

Restart note: during the Challenger-first restart, this rubric is `legacy_reference` by default. Use it only when the active episode constraint ledger imports or activates its review criteria for the scoped short.

## Checklist

### 1. Canonical Identity

- Does the subject still read immediately as the intended thing?
- Are the parts that define that subject class still believable?

If no:
- disposition is `reject`

## 2. Anomaly Plausibility

- Does the wrongness read as a believable wrong state for this subject?
- Would a human viewer read it as a system contradiction rather than a random defect?

If no:
- usually `tighten`
- `reject` if it reads as nonsense or corruption

## 3. Anomaly Legibility

- Can the anomaly be seen without reading the prompt?
- Is it dominant enough to matter but local enough to stay believable?

If no:
- disposition is `tighten`

## 4. Camera Validity

- Does the chosen camera angle actually expose the failure mechanism?
- Is the image too wide, too vague, or too cropped to show what is wrong?

If no:
- disposition is `tighten`

## 5. Source Anchor Fidelity

- Does the still still read as the named research artifact, scene family, or sourced carrier?
- Would a viewer still infer the intended subject class without needing the prompt text?
- Has the carrier collapsed into a generic folder, tray, table prop, or anonymous evidence-room object?

If no:
- usually `reject`
- `tighten` only when the anchor is still partially legible and the fix is straightforward

## 6. Artifact Leakage

- Does the anomaly look like warped geometry, broken anatomy, or sampler damage?
- Does the image contain obvious pasted control assets or compositing artifacts?
- If the failure only appears once the still is animated, does it clearly come from the source still rather than from the motion prompt?

If yes:
- disposition is `reject`

If the motion failure is inherited from the source still:
- disposition is `tighten` on the still first, then rerender motion from the corrected still
- do not keep trying new motion prompts against the broken source image

## 7. Text / Logo Leakage

- Is there readable brand text, UI text, logo leakage, or pseudo-labeling?

If yes:
- usually `reject`
- `diagnostic only` is acceptable if the image is still useful as a learning example

## 8. Final Disposition

- `keep`
  - subject is canonical
  - source anchor remains recognizable
  - anomaly is plausible
  - anomaly is legible
  - no material artifact leakage

- `tighten`
  - subject is usable
  - source anchor is still mostly intact
  - anomaly is too subtle, too vague, or hidden by camera choice
  - next move should be prompt/camera/anomaly-carrier revision

- `diagnostic only`
  - the image taught something valuable
  - but it is not a keeper because one or more key checks failed

- `reject`
  - subject identity collapsed
  - anchor match failed or drifted into anonymous evidence-room logic
  - anomaly reads as model corruption
  - warped geometry or artifact leakage dominates
  - text/logo leakage materially damages the frame

## 9. Selective Archival Signal Texture

For archival/broadcast-linked motion, texture is reviewed after the underlying motion clip is already `keep`.

- Does the texture remain full-bleed with no TV frame, matte, rounded mask, border, reduced image area, or audio?
- Does the YouTube survivability proxy preserve subject readability?
- Does the treatment feel like premium archival signal texture rather than a fake CRT gimmick?
- Does it preserve faces, room detail, vehicle/machinery geometry, plume, debris, and other story-critical detail?

If no:
- disposition is `tighten` or `reject` for the texture pass, not for the underlying motion clip unless the clip itself failed
- failure mode is `texture_invisible_no_reviewable_historical_signal`, `historical_signal_overpowering_subject`, `compression_shimmer_or_mud`, `historical_signal_cheese`, `detail_loss_from_signal_texture`, `era_mismatch`, or `global_historical_signal_misapplied`

## 10. Promotion Sanity Check

- A motion clip cannot be `keep` if the source still is anything other than `keep`.
- A reel cannot be a keeper reel unless every included clip is `keep`.
- If any included clip is `tighten`, `diagnostic only`, or `reject`, classify the reel as a `mixed review reel`.

## Hard Reject Rule

“Warped geometry / model corruption” is a hard reject even if the anomaly is more legible.

Legibility does not compensate for a subject that has stopped being credible.

This applies to motion as well. If anatomy corruption survives into motion, the lane is unresolved until the still is repaired upstream.

`anonymous evidence-room drift` is also a hard reject unless the packet explicitly records a DP-approved non-literal exception.

## Recommended Review Order

1. Canonical identity
2. Anomaly plausibility
3. Anomaly legibility
4. Camera validity
5. Source anchor fidelity
6. Artifact leakage
7. Text/logo leakage
8. Selective archival signal texture, when applicable
9. Disposition

Do not skip directly to “do I like it.” Decide whether it is trustworthy first.
