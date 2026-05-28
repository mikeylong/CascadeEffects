# Hyatt N6 Chapter Motion Smoothing Rough Proof

Status: tighten, superseded by `hyatt_living_cover_html_rough_proof_n6_challenger_staged_transition_20260517T214408Z`.

Review URL: http://127.0.0.1:8844/player.html

## What Changed

- Invalidated for MP4 render because the broad `3s` pre-boundary / `5s` post-boundary blend did not match the Challenger staged transition at `01:31/01:32`.
- Smoothed source-art zoom, slide, and warmth changes across chapter boundaries with `visual_motion_transition_model_v1`.
- Blends previous and next chapter visual states with a 3-second pre-boundary lead-in, 5-second post-boundary release, and smoothstep easing.
- Preserved exact rail title/context/caption timing, reduced rail opacity, repaired live-load audio, script-locked captions, N6 source art, camera flashes, balloons, and Challenger-style music.
- No MP4, publish-readiness package, upload receipt, or YouTube action was created.

## Review Question

Do the chapter background zoom/slide transfers feel smooth and intentional without competing with the right-rail chapter change?
