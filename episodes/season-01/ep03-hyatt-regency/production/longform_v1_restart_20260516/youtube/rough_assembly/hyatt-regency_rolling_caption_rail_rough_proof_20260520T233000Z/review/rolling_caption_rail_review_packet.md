# Hyatt Regency Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `hyatt-regency`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt-regency_rolling_caption_rail_rough_proof_20260520T233000Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep3_Hyatt-Regency/production/longform_v1_restart_20260516/youtube/rough_assembly/hyatt-regency_rolling_caption_rail_rough_proof_20260520T233000Z/rough_assembly_manifest.json`
- Rail preset: `fixed_16x9_right_rail_v1`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Caption window role: `middle_two_thirds_right_rail`
- Caption blur scope: `caption_window_only`
- Caption highlight source: `living_cover_cue_map_key_phrases`
- Caption palette source: `sampled_episode_backplate`

## Gate Handling

- Action: `supersede_publish_final_surfaces_create_successor_rough_proof`
- Status: `rolling_caption_rail_rough_assembly_review_ready_pending_human_keep`
- Source art rollback: not opened by default because the rail footprint is unchanged.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until this refreshed rough proof receives human `keep`.

## Human Review Focus

- Captions roll smoothly through the middle two-thirds of the right rail with no seek jumps or layout jitter.
- The blur/fill appears behind captions only, not behind the entire right rail.
- Old previous/upcoming context rows are absent.
- Key phrase highlights brighten from sampled color and fade back without karaoke, boxes, badges, glow, progress bars, or timecode.
- At the end-screen transition, captions continue upward and the caption window/blur/text/highlights fade fully out before YouTube target geometry.
- Right-rail safe space remains valid against the kept backplate.

## Key Phrase Span Drafts

- 1981 about 1600 people gathered (1.256 to 4.056s): #ffd19a
- was tea dance (10.46 to 11.96s): #ffd19a
- year The atrium was one (13.725 to 16.249s): #ffd19a
- suspended walkways crossing overhead the (19.915 to 22.539s): #ffd19a
- 705 the fourth-floor walkway collapsed (27.366 to 30.166s): #ffd19a

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
