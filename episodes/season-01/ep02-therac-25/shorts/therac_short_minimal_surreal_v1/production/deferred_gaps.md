# Therac-25 Deferred Short Gaps

## Deferred Short Gap

- `episode_id`: `therac-25`
- `short_id`: `therac_short_minimal_surreal_v1`
- `beat_id`: `beat_01_denial_initial`, `beat_02_interlocks_removed`, `beat_04_reused_code`, `beat_06_no_safety_layer`
- `archetype`: `mixed room_or_interior and single_object_or_device`
- `carrier`: `still-hold proof coverage from approved still keepers`
- `passes_exhausted`: `0`
- `current_disposition`: `diagnostic only`
- `failure_mode`: `the beats are visually covered for timing review, but they are not promoted motion clips`
- `source_baked_issue`: `false`
- `best_attempt_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__proof.mp4`
- `next_carrier`: `after timing approval, open beat-local motion from the current keeper stills rather than changing the visual order`
- `reopen_condition`: `user accepts the mixed proof pacing and shot sequence`
- `notes`: `The still-hold lanes are intentionally included only to make the full 60.975601s clean-script short reviewable against the corrected audio. They do not promote the short to keeper status.`

## Deferred Short Gap

- `episode_id`: `therac-25`
- `short_id`: `therac_short_minimal_surreal_v1`
- `beat_id`: `beat_03_race_condition_wrong_state`, `beat_05_reports_denial`
- `archetype`: `single_object_or_device and single_human_figure`
- `carrier`: `approved 5.04s motion clips normalized to longer spoken beats`
- `passes_exhausted`: `0`
- `current_disposition`: `diagnostic only`
- `failure_mode`: `the current imported motion is keep, but each normalized segment freezes at the tail because the approved source clip is shorter than the target beat`
- `source_baked_issue`: `false`
- `best_attempt_path`: `/Users/mike/Viz_CascadeEffects/workflows/generated/shorts/therac_short_minimal_surreal_v1/20260417T040035Z/20260417T040035Z__proof.mp4`
- `next_carrier`: `split the visual beat or render longer motion from the same keeper still if the tail freeze distracts in review`
- `reopen_condition`: `user accepts the beat placement but flags the freeze-tail as too static`
- `notes`: `The freeze-tail is acceptable for a timing proof, not for a final keeper short.`
