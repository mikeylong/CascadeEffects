# Challenger Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `challenger`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_rough_proof_20260520T233000Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/production/longform_v3_20_25min/youtube/rough_assembly/challenger_rolling_caption_rail_rough_proof_20260520T233000Z/rough_assembly_manifest.json`
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

- was smoke from the aft (5.58 to 8.379999999999999s): #ffe0a6
- Then stopped (15.194 to 16.694s): #ffe0a6
- The vehicle climbed (20.181 to 21.681s): #ffe0a6
- The machinery the mission appeared (23.527 to 26.327s): #ffe0a6
- then the public version could (34.945 to 37.109s): #ffe0a6

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
