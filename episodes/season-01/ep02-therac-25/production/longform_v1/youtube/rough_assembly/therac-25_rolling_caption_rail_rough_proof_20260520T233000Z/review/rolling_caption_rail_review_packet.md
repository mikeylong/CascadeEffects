# Therac-25 Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `therac-25`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac-25_rolling_caption_rail_rough_proof_20260520T233000Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/production/longform_v1/youtube/rough_assembly/therac-25_rolling_caption_rail_rough_proof_20260520T233000Z/rough_assembly_manifest.json`
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

- room The door closed (2.582 to 4.409s): #bff4cf
- machine the next room (7.141 to 9.05s): #bff4cf
- She has entered the treatment (11.434 to 13.077s): #bff4cf
- She presses the key activate (16.142 to 18.085s): #bff4cf
- error The patient feels sudden (24.755 to 27.5s): #bff4cf

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
