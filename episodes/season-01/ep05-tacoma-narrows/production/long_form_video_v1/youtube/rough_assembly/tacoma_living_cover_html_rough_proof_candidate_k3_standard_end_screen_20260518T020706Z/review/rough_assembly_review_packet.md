# Tacoma K3 Living Cover Rough Proof Review - Standard End Screen Repair

## Status
- Gate: `rough_assembly_gate`
- Status: `review_ready_human_keep_pending`
- Human ask: review the rebuilt K3 Living Cover `player.html` with the Challenger/Therac standard end-screen template and choose `keep`, `tighten`, or `reject`.
- Final MP4, publish readiness, YouTube upload, and public release remain blocked.

## Active Source Art
- Candidate: `candidate_k3_roadway_wide_stance`
- Plate: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_standard_end_screen_20260518T020706Z/assets/source_art/candidate_k3_roadway_wide_stance_1920x1080.png`
- SHA-256: `8f85d657d6a2573ddeaf637e468d4a8b2db4a20b2017b369591579f086e6246c`
- Source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_standard_end_screen_20260518T020706Z/references/source_art_manifest.json`

## Preserved Production Inputs
- Audio: Challenger-style music-only intro, voice offset, fade tail, and full outro review mix.
- Captions: regenerated packet-local script-locked VTT/SRT sidecars using WhisperX timing only.
- Visual system: `living_cover_system_v1`, `fixed_16x9_right_rail_v1`.
- Repairs carried forward: intro readability, right-rail opacity balance, end-screen text suppression.
- Successor repair: replaces the ad hoc one-video/rectangular-subscribe end screen with `challenger_titleless_end_screen_overlay_on_living_cover_v1`.

## Review Reads
- K3 backplate loaded in the viewer-facing proof.
- Candidate G runtime source-art reference absent from `player.html`.
- Captions stay inside the right rail and are suppressed before voice start and after outro start.
- No standalone cue labels, diagnostic overlays, cyan signal traces, or out-of-rail story text.
- The lower right rail does not become an opaque column below the active scene text.
- End-screen target geometry uses the Challenger/Therac titleless three-target template:
  left video `[78,382,758,765]`, right video `[1162,382,1842,765]`, center subscribe `[814,429,1106,721]`.
- Story, chapter, context, caption, and cue text are suppressed in the end-screen window.

## Downstream Locks
- `may_render_final_mp4: false`
- `may_youtube_action: false`
- `public_release_ready: false`
