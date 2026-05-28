# Tacoma K3 Large-Drop Beaded Glass-Rain Rough Proof Review

Status: rough_assembly_review_ready_human_keep_pending

Active review URL: http://127.0.0.1:8858/player.html

## Reference

The prior beaded-pane treatment followed the supplied weather-app glass reference, but the droplets read too small and distant. This successor keeps the same viewer-facing rain-on-glass direction and scales the droplets up so they read as foreground windshield/window beads over the image.

Reference contact sheet: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_beaded_glass_large_drops_20260519T005927Z/qa/reference/reference_screen_recording_contact_sheet.png

## What Changed

- Replaced `foreground_glass_rain_beaded_pane_v3` with `foreground_glass_rain_large_beaded_pane_v4`: 132 larger bead-like drops, 28 short runners, droplet radius range 4-20px, terminal-drop range 4-12px.
- Slowed the field slightly so the bigger drops slide down the screen instead of becoming distant rain noise.
- Preserved the intro clock repair: chapter visuals and captions stay on `storyTime`; glass-rain motion uses absolute `audioTime` from `t=0`.
- Preserved K3 source art, repaired wind-tunnel VO, script-locked rail captions, media-player caption track, actual-outro prelap mix, right-rail opacity repair, Challenger/Therac titleless end screen, and `challenger_staged_visual_transition_v1`.
- Masked the glass-rain layer out of the fixed right rail and caption region.

## Review Ask

Choose `keep`, `tighten`, or `reject` for the large-drop beaded glass-rain rough proof. A `keep` can open final MP4 render planning only; it does not upload or publish anything.

## QA

- Browser QA: pass
- Pre-VO motion: pass between `t=0.00s` and `t=0.85s`
- Motion clock: pass, `window.__glassRainStateAt(time).motionClock = "audio_time_from_zero"`
- Foreground drop scale: pass, radius range 4-20px and terminal drops 4-12px
- Large beaded-pane variant: pass
- Review strip: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_beaded_glass_large_drops_20260519T005927Z/qa/glass_rain_review_strip.png
- Required reads: foreground drop scale, reference alignment, intro motion, motion clock, beaded-pane variant, image-only mask, right-rail exclusion, caption legibility, source-plate geometry preservation, deterministic glass rain, debug-overlay absence, range scrub, staged chapter transitions, end screen, captions, and byte-range media all pass.

## Locks

Final MP4, publish readiness, YouTube upload, and public release remain blocked.
