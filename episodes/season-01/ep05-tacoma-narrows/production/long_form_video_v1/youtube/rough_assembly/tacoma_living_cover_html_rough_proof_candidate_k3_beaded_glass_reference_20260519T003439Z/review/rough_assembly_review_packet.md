# Tacoma K3 Beaded-Pane Glass-Rain Rough Proof Review

Status: rough_assembly_review_ready_human_keep_pending

Active review URL: http://127.0.0.1:8858/player.html

## Reference

User supplied a 16.177s screen recording of a weather-app style glass pane. The recording has no audio stream, so transcription is not applicable; frame review shows dense bead-like droplets, subtle lens highlights/shadows, slower downward motion, and only a smaller number of short runners.

Reference contact sheet: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_beaded_glass_reference_20260519T003439Z/qa/reference/reference_screen_recording_contact_sheet.png

## What Changed

- Replaced the rivulet-led treatment with `foreground_glass_rain_beaded_pane_v3`: 240 bead-like drops and 40 short runners.
- Kept the intro clock repair: chapter visuals and captions stay on `storyTime`; glass-rain motion uses absolute `audioTime` from `t=0`.
- Preserved K3 source art, repaired wind-tunnel VO, script-locked visible rail captions, media-player caption track, actual-outro prelap mix, right-rail opacity repair, Challenger/Therac titleless end screen, and `challenger_staged_visual_transition_v1`.
- Masked the glass-rain layer out of the fixed right rail and caption region.

## Review Ask

Choose `keep`, `tighten`, or `reject` for the beaded-pane glass-rain rough proof. A `keep` can open final MP4 render planning only; it does not upload or publish anything.

## QA

- Browser QA: pass
- Pre-VO motion: pass between `t=0.00s` and `t=0.85s`
- Motion clock: pass, `window.__glassRainStateAt(time).motionClock = "audio_time_from_zero"`
- Beaded-pane variant: pass
- Review strip: /Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_beaded_glass_reference_20260519T003439Z/qa/glass_rain_review_strip.png
- Required reads: reference alignment, intro motion, motion clock, beaded-pane variant, image-only mask, right-rail exclusion, caption legibility, source-plate geometry preservation, deterministic glass rain, debug-overlay absence, range scrub, staged chapter transitions, end screen, captions, and byte-range media all pass.

## Locks

Final MP4, publish readiness, YouTube upload, and public release remain blocked.
