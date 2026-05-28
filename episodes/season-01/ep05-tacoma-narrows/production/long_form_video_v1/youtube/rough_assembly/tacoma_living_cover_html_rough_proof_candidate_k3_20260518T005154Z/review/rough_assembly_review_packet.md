# Tacoma K3 Living Cover Rough Proof Review

## Status
- Gate: `rough_assembly_gate`
- Status: `review_ready_human_keep_pending`
- Human ask: review the rebuilt K3 Living Cover `player.html` and choose `keep`, `tighten`, or `reject`.
- Final MP4, publish readiness, YouTube upload, and public release remain blocked.

## Active Source Art
- Candidate: `candidate_k3_roadway_wide_stance`
- Plate: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_20260518T005154Z/assets/source_art/candidate_k3_roadway_wide_stance_1920x1080.png`
- SHA-256: `8f85d657d6a2573ddeaf637e468d4a8b2db4a20b2017b369591579f086e6246c`
- Source-art manifest: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/production/long_form_video_v1/youtube/rough_assembly/tacoma_living_cover_html_rough_proof_candidate_k3_20260518T005154Z/references/source_art_manifest.json`

## Preserved Production Inputs
- Audio: Challenger-style music-only intro, voice offset, fade tail, and full outro review mix.
- Captions: regenerated packet-local script-locked VTT/SRT sidecars using WhisperX timing only.
- Visual system: `living_cover_system_v1`, `fixed_16x9_right_rail_v1`.
- Repairs carried forward: intro readability, right-rail opacity balance, end-screen text suppression.

## Review Reads
- K3 backplate loaded in the viewer-facing proof.
- Candidate G runtime source-art reference absent from `player.html`.
- Captions stay inside the right rail and are suppressed before voice start and after outro start.
- No standalone cue labels, diagnostic overlays, cyan signal traces, or out-of-rail story text.
- The lower right rail does not become an opaque column below the active scene text.
- End-screen target geometry is static and story text is suppressed in the end-screen window.

## Downstream Locks
- `may_render_final_mp4: false`
- `may_youtube_action: false`
- `public_release_ready: false`
