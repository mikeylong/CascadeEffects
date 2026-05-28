# Review Rubric

Use this rubric for every future proof packet before deciding whether to keep rendering or move on.

Then apply `judgment/promotion_workflow.md` to decide whether the result may advance to motion, reel assembly, or the keeper registry.

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

## 5. Artifact Leakage

- Does the anomaly look like warped geometry, broken anatomy, or sampler damage?
- Does the image contain obvious pasted control assets or compositing artifacts?
- If the failure only appears once the still is animated, does it clearly come from the source still rather than from the motion prompt?

If yes:
- disposition is `reject`

If the motion failure is inherited from the source still:
- disposition is `tighten` on the still first, then rerender motion from the corrected still
- do not keep trying new motion prompts against the broken source image

## 6. Text / Logo Leakage

- Is there readable brand text, UI text, logo leakage, or pseudo-labeling?

If yes:
- usually `reject`
- `diagnostic only` is acceptable if the image is still useful as a learning example

## 7. Final Disposition

- `keep`
  - subject is canonical
  - anomaly is plausible
  - anomaly is legible
  - no material artifact leakage

- `tighten`
  - subject is usable
  - anomaly is too subtle, too vague, or hidden by camera choice
  - next move should be prompt/camera/anomaly-carrier revision

- `diagnostic only`
  - the image taught something valuable
  - but it is not a keeper because one or more key checks failed

- `reject`
  - subject identity collapsed
  - anomaly reads as model corruption
  - warped geometry or artifact leakage dominates
  - text/logo leakage materially damages the frame

## 8. Promotion Sanity Check

- A motion clip cannot be `keep` if the source still is anything other than `keep`.
- A reel cannot be a keeper reel unless every included clip is `keep`.
- If any included clip is `tighten`, `diagnostic only`, or `reject`, classify the reel as a `mixed review reel`.

## Hard Reject Rule

“Warped geometry / model corruption” is a hard reject even if the anomaly is more legible.

Legibility does not compensate for a subject that has stopped being credible.

This applies to motion as well. If anatomy corruption survives into motion, the lane is unresolved until the still is repaired upstream.

## Recommended Review Order

1. Canonical identity
2. Anomaly plausibility
3. Anomaly legibility
4. Camera validity
5. Artifact leakage
6. Text/logo leakage
7. Disposition

Do not skip directly to “do I like it.” Decide whether it is trustworthy first.
