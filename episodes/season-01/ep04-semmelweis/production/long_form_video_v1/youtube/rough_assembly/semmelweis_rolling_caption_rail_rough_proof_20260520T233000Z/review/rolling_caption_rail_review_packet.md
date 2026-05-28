# Semmelweis Rolling Caption Rail Rough Proof

## Review Target

- Episode ID: `semmelweis`
- Player: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/youtube/rough_assembly/semmelweis_rolling_caption_rail_rough_proof_20260520T233000Z/player.html`
- Manifest: `/Users/mike/Episodes_CascadeEffects/Ep4_Semmelweis/production/long_form_video_v1/youtube/rough_assembly/semmelweis_rolling_caption_rail_rough_proof_20260520T233000Z/rough_assembly_manifest.json`
- Rail preset: `fixed_16x9_right_rail_v1`
- Rail content model: `rolling_caption_anchor_v1`
- Caption display model: `rolling_rail_caption_window_v1`
- Caption window role: `middle_two_thirds_right_rail`
- Caption blur scope: `caption_window_only`
- Caption highlight source: `living_cover_cue_map_key_phrases`
- Caption palette source: `sampled_episode_backplate`

## Gate Handling

- Action: `move_forward_after_current_prerequisite_keep`
- Status: `rolling_caption_rail_rough_assembly_blocked_pending_current_prerequisite_keep`
- Source art rollback: not opened by default because the rail footprint is unchanged.
- Downstream gates: final assembly, publish readiness, and YouTube action remain blocked until this refreshed rough proof receives human `keep`.
- Prerequisite blocker: current ambient/effects and downstream music/motion prerequisites must receive keep before rough assembly can be keep-ready

## Human Review Focus

- Captions roll smoothly through the middle two-thirds of the right rail with no seek jumps or layout jitter.
- The blur/fill appears behind captions only, not behind the entire right rail.
- Old previous/upcoming context rows are absent.
- Key phrase highlights brighten from sampled color and fade back without karaoke, boxes, badges, glow, progress bars, or timecode.
- At the end-screen transition, captions continue upward and the caption window/blur/text/highlights fade fully out before YouTube target geometry.
- Right-rail safe space remains valid against the kept backplate.

## Key Phrase Span Drafts

- The evidence arrived before the (12 to 14.8s): #dff0a8
- The cost was paid patients (20 to 22.8s): #dff0a8
- The evidence arrived before the (28.4 to 31.2s): #dff0a8
- The cost was paid patients (36.8 to 39.599999999999994s): #dff0a8

## Required Response

Reply with exactly one disposition: `keep`, `tighten`, or `reject`.
