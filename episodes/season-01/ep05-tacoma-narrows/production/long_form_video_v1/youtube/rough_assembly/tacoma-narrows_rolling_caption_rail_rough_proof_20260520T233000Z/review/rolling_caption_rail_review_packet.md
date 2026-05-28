# Tacoma Narrows Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `tacoma-narrows`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_rough_proof_20260520T233000Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma-narrows_rolling_caption_rail_rough_proof_20260520T233000Z/rough_assembly_manifest.json`
- Rail preset: `fixed_16x9_right_rail_v1`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Caption window role: `middle_two_thirds_right_rail`
- Caption blur scope: `caption_window_only`
- Caption highlight source: `living_cover_cue_map_key_phrases`
- Caption palette source: `sampled_episode_backplate`

## Gate Handling

- Action: `refresh_current_rough_review_ready_proof`
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

- collapsed into Puget Sound (13.618 to 15.121s): #b6e7f3
- Four months later was gone (17.024 to 19.824s): #b6e7f3
- was measured miles per hour (24.175 to 25.675s): #b6e7f3
- hour near the bridge's east (29.644 to 32.443999999999996s): #b6e7f3
- hour What could not survive (39.852 to 42.651999999999994s): #b6e7f3

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
