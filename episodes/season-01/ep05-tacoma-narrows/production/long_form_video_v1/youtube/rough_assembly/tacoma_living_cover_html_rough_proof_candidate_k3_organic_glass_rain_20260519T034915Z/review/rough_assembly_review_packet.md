# Tacoma K3 Organic Glass-Rain Rough Proof Review

Status: rough_assembly_review_ready_human_keep_pending

Active review URL: http://127.0.0.1:8858/player.html

## What Changed

- Preserved the flipped K3 backplate layout probe so the bridge tower and long-span story information remain outside the fixed right rail.
- Replaced `foreground_glass_rain_large_beaded_pane_v4` with `foreground_glass_rain_organic_pane_v5`.
- Changed the rain shape language from circular beads/radial lens drops to irregular teardrops, elongated terminal drops, and rivulet paths.
- Preserved repaired wind-tunnel VO, script-locked rail captions, media-player caption track, actual-outro prelap mix, right-rail opacity repair, Challenger/Therac titleless end screen, and `challenger_staged_visual_transition_v1`.

## Shape Repair

The previous proof read as bubbles because the renderer used circular ellipses, circular terminal drops, and radial gradient highlights. This successor removes those spherical primitives from the glass-rain renderer and exposes explicit QA fields through `window.__glassRainStateAt(time)`:

- `shapeModel: irregular_teardrop_and_rivulet_paths`
- `dropAspectRatioRange: [2.2, 4.2]`
- `sphericalDropPolicy: forbidden_no_circular_bead_bodies`
- `terminalShapeModel: elongated_teardrop_path_not_circle`
- `motionClock: audio_time_from_zero`

## Source-Art Note

This remains a review-only rough proof over the human-kept K3 ImageGen plate with deterministic horizontal flip. It does not create a final MP4 or publish asset.

Original K3 plate: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_organic_glass_rain_20260519T034915Z/assets/source_art/candidate_k3_roadway_wide_stance_1920x1080.png

Flipped review plate: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_organic_glass_rain_20260519T034915Z/assets/source_art/candidate_k3_roadway_wide_stance_flipped_1920x1080.png

## Review Ask

Choose `keep`, `tighten`, or `reject` for the flipped-backplate organic glass-rain rough proof. A `keep` can open final MP4 render planning only; it does not upload or publish anything.

## QA

- Browser QA: pass
- Backplate horizontal flip: pass
- Right-rail story space: pass
- Foreground rain scale: pass, large foreground width/height ranges preserved
- Non-spherical rain shape: pass
- Organic teardrop/rivulet model: pass
- Bubble artifact absence: pass, no radial/circular bubble primitives in the glass renderer
- Terminal drop shape: pass, elongated teardrop paths
- Pre-VO glass motion: pass between `t=0.00s` and `t=0.85s`
- Review strip: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_organic_glass_rain_20260519T034915Z/qa/glass_rain_review_strip.png
- Required prior reads remain passing: K3 loaded, Candidate G absent, image-only mask, right-rail exclusion, caption legibility, source-plate geometry preservation, deterministic glass rain, debug-overlay absence, range scrub, staged chapter transitions, end screen, captions, and byte-range media.

## Locks

Final MP4, publish readiness, YouTube upload, and public release remain blocked.
