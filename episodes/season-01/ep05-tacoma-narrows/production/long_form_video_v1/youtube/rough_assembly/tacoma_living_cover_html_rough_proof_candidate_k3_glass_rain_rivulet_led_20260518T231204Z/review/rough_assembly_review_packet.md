# Tacoma K3 Rivulet-Led Glass-Rain Rough Proof Review

Status: rough_assembly_review_ready_human_keep_pending

Active review URL: http://127.0.0.1:8858/player.html

## What Changed

- Replaced the prior glass-rain treatment with `foreground_glass_rain_rivulet_led_v2`: fewer tiny specks, more readable sliding rivulets and pane-of-glass trails.
- Fixed the intro clock: chapter visuals and captions stay on `storyTime`, while glass-rain motion now uses absolute `audioTime` from `t=0`, so the layer moves during the music-only intro.
- Preserved K3 source art, repaired wind-tunnel VO, script-locked visible rail captions, media-player caption track, actual-outro prelap mix, right-rail opacity repair, Challenger/Therac titleless end screen, and `challenger_staged_visual_transition_v1`.
- Masked the glass-rain layer out of the fixed right rail and caption region.

## Review Ask

Choose `keep`, `tighten`, or `reject` for the rivulet-led glass-rain rough proof. A `keep` can open final MP4 render planning only; it does not upload or publish anything.

## QA

- Browser QA: pass
- Pre-VO motion: pass between `t=0.00s` and `t=0.85s`
- Motion clock: pass, `window.__glassRainStateAt(time).motionClock = "audio_time_from_zero"`
- Rivulet strip: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_glass_rain_rivulet_led_20260518T231204Z/qa/glass_rain_review_strip.png
- Required reads: intro motion, motion clock, rivulet variant, image-only mask, right-rail exclusion, caption legibility, source-plate geometry preservation, deterministic glass rain, debug-overlay absence, range scrub, staged chapter transitions, end screen, captions, and byte-range media all pass.

## Locks

Final MP4, publish readiness, YouTube upload, and public release remain blocked.
