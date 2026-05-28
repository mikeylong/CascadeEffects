# Challenger Candidate B Seven-Astronaut Regeneration

Status: `experiment_review_ready_candidate_a_tighten_pending_human_keep_or_tighten`

This is a successor source-art experiment targeting prior `candidate_b_wide_right_rail_safe_observers`: top of tower visible, red beacon, long right-side pad/crawlerway depth, practical-light atmosphere, and rail-safe dark sky. The generic observer crowd is replaced by anonymous back-facing astronauts in blue flight suits.

## Human QA Correction

Candidate A was originally misread as seven figures. Human review caught that it shows eight foreground astronauts, so it now hard-fails `seven_astronaut_foreground_read` and is not recommended.

## Candidate Reads

| Candidate | Status | Main strength | Hard-read summary |
| --- | --- | --- | --- |
| `candidate_a_candidate_b_composition_exact_seven` | `tighten_count_drift_not_recommended` | visually close to the requested reference, but hard-fails the foreground count: eight astronauts are visible | tighten_count_drift_eight_foreground_astronauts_visible / observed count 8; tower top read: pass_tower_top_and_red_beacon_visible |
| `candidate_b_clean_rail_depth_exact_seven` | `review_ready_pending_human_keep_or_tighten` | recommended passing candidate: exactly seven astronauts, strong right-side rail safety, clean pad depth, tower top visible | pass_exactly_seven_foreground_astronauts_visible / observed count 7; tower top read: pass_tower_top_and_red_beacon_visible |
| `candidate_c_wet_pad_atmosphere_exact_seven` | `review_ready_pending_human_keep_or_tighten` | strong wet-surface ambience and tower visibility, seven astronauts, slightly less open right rail than A/B | pass_exactly_seven_foreground_astronauts_visible / observed count 7; tower top read: pass_tower_top_and_red_beacon_visible |

## Recommendation

`candidate_b_clean_rail_depth_exact_seven` is now recommended for human review because it is the strongest passing candidate after the Candidate A count correction: exactly seven foreground astronauts, tower top/red beacon visible, long right-side pad depth, and clean rail-safe sky.

## Gate Note

No candidate is `keep`. The packet is `experiment_only`; it does not touch current final, publish-readiness, upload, schedule, or public release state.

Review HTML: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_experiment/challenger_candidate_b_seven_astronaut_regeneration_20260519T180814Z/review/review.html`
Manifest: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/source_art_experiment/challenger_candidate_b_seven_astronaut_regeneration_20260519T180814Z/source_art_experiment_manifest.json`
