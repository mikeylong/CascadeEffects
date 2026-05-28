# Tacoma K3 Flipped-Backplate Large-Drop Rough Proof Review

Status: rough_assembly_review_ready_human_keep_pending

Active review URL: http://127.0.0.1:8858/player.html

## What Changed

- Flipped the kept K3 backplate horizontally as `horizontal_flip_layout_probe_v1` so the bridge tower and long-span story information sit in the open left/story area instead of under the fixed right rail.
- Preserved the large foreground glass-rain treatment: 132 larger bead-like drops, 28 short runners, 4-20px drop radius, 4-12px terminal drops.
- Preserved repaired wind-tunnel VO, script-locked rail captions, media-player caption track, actual-outro prelap mix, right-rail opacity repair, Challenger/Therac titleless end screen, and `challenger_staged_visual_transition_v1`.

## Source-Art Note

This packet is a review-only deterministic layout probe over the human-kept K3 ImageGen plate. It does not create a new source-art keep by itself. If this orientation is kept, the final-render path should record the flipped derivative as the active rough-proof source asset while preserving the original K3 provenance.

Original K3 plate: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_flipped_backplate_large_drops_20260519T011711Z/assets/source_art/candidate_k3_roadway_wide_stance_1920x1080.png

Flipped review plate: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_flipped_backplate_large_drops_20260519T011711Z/assets/source_art/candidate_k3_roadway_wide_stance_flipped_1920x1080.png

## Review Ask

Choose `keep`, `tighten`, or `reject` for the flipped-backplate large-drop rough proof. A `keep` can open final MP4 render planning only; it does not upload or publish anything.

## QA

- Browser QA: pass
- Backplate horizontal flip: pass
- Right-rail story space: pass, tower/story mass repositioned out from under fixed rail
- Foreground drop scale: pass, radius range 4-20px and terminal drops 4-12px
- Pre-VO glass motion: pass between `t=0.00s` and `t=0.85s`
- Review strip: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_flipped_backplate_large_drops_20260519T011711Z/qa/glass_rain_review_strip.png
- Required reads: flipped backplate, right-rail story space, K3 loaded, Candidate G absent, large foreground glass rain, image-only mask, right-rail exclusion, caption legibility, source-plate geometry preservation for glass layer, deterministic glass rain, debug-overlay absence, range scrub, staged chapter transitions, end screen, captions, and byte-range media all pass.

## Locks

Final MP4, publish readiness, YouTube upload, and public release remain blocked.
