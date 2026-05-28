# Tacoma Narrows Pass 07 CRT Visible Scanline Final Review

- `episode_id`: `tacoma-narrows`
- `short_id`: `tacoma_short_scoped_v1`
- `candidate_id`: `house_crt_visible_scanline_pass_07`
- `stage`: `video final`
- `status`: `review_ready`
- `human_keep_status`: `pending`
- `may_advance`: `false`
- `created_at`: `2026-05-16T22:58:39Z`

## Candidate

- Captioned final: `/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/final_exports/tacoma-narrows_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/final/tacoma-narrows__house_crt_visible_scanline_signal_interruption_captioned_final.mp4`
- SHA-256: `ebecebef84bde5e915d4b4927f655128712f17545d89a36ca19a260e992c9ded`
- No-audio final: `/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/final_exports/tacoma-narrows_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/final/tacoma-narrows__house_crt_visible_scanline_signal_interruption_captioned_no_audio.mp4`
- SHA-256: `2d0867f5879feaba999c24ce5020cc44a448449df848b2825f651001bcf06bbe`

## Probe Facts

- Captioned final: `1080x1920`, `30/1 fps`, H.264 video, AAC mono audio, `62.233333s`.
- No-audio final: `1080x1920`, `30/1 fps`, H.264 video only, `62.233333s`.
- Captioned decode: `pass`, empty stderr.
- No-audio decode: `pass`, empty stderr.
- Probe sidecars:
  - `/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/final_exports/tacoma-narrows_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/review_sidecars/pass07_reconstructed_review_only/ffprobe_captioned_final.json`
  - `/Users/mike/Viz_CascadeEffects/references/episodes/tacoma-narrows/shorts/tacoma_short_scoped_v1/motion_video_proof/pass_01_source_led/final_exports/tacoma-narrows_house_crt_clean_source_lineage_visible_scanline_first8_pass_07/20260429T_house_crt_visible_scanline_first8_pass07_y24/review_sidecars/pass07_reconstructed_review_only/ffprobe_no_audio_final.json`

## QA References

- Contact sheet: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/shorts/tacoma_short_scoped_v1/production/qa/pass07_crt_visible_scanline_review/pass07_crt_visible_scanline_review_contact_sheet.jpg`
- Sample frame root: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/shorts/tacoma_short_scoped_v1/production/qa/pass07_crt_visible_scanline_review/frames`
- Sampled moments: opening, bridge motion, wind-not-extraordinary caption, torsion setup, feedback-loop caption, engineers-motion line, motif caption, and outro tail.
- Existing pass-07 review media remains available under the candidate `review/` folder, including signal-interruption sheets and final-tail sheet.

## Audio And Caption Read

- Audio package: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_short_scoped_v1/audio_package.json`
- Audio package SHA-256: `a461e60f9218453ae23bac697000450b470307ecc1ef47887c5cdb9606d214ff`
- Packaged WAV: `/Users/mike/Episodes_CascadeEffects/Ep5_Tacoma-Narrows/shorts/tacoma_short_scoped_v1/final/tacoma_short_scoped_v1.wav`
- Packaged WAV SHA-256: `b623773e1e3d752c29659668492309996da1f48145a4f8ac8ef1d3a18991bcbb`
- Caption source SRT: `/Users/mike/Audio_CascadeEffects/tmp/ep5_tacoma_narrows_short_scoped_v1/transcripts_mastered/tacoma_short_scoped_v1.diarized.srt`
- Caption source SHA-256: `9865309a96e5cbacade2b758bf85ce992e152bcea42c82c9849b9c044843ec28`
- Motif source line present: `Small causes, massive consequences.`
- Ending cadence read from active manifest/audio package: `pass`.

## Freeze And Tail Read

- Full final-tail scan from `55.000s` with `freezedetect d=0.15` found five short `0.166667s` freeze-like events.
- Narrow outro-tail scan from `58.746s` to `62.246s` with `freezedetect d=0.15` found two short `0.166667s` events.
- Narrow outro-tail scan from `58.746s` to `62.246s` with `freezedetect d=0.50` found no events.
- Review note: these are short signal/hold-like events, not a long endpoint freeze. Human/DP should still inspect the outro tail before keep.

## Blockers

- Human/DP keep is pending.
- The original pass-07 folder did not contain final export JSON/MD/SRT sidecars; this packet reconstructs review-only sidecars.
- The old YouTube publish package is diagnostic-only because it points to the superseded pass07 no-freeze final, not this CRT visible-scanline candidate.
- Source inventory JSON paths recorded in TOML are missing on disk and should be repaired or regenerated before any publish package is rebuilt.
- Rights/fair-use human acceptance and YouTube claim check remain required before any public release.

## Review Ask

Decide one of:

- `keep`: accept this pass-07 CRT visible-scanline final. Next step becomes rebuilding the YouTube Shorts publish package from this exact candidate, then running package validation. Upload remains blocked until explicit private-upload approval.
- `tighten`: route back to `youtube_shorts_final_export_v1` with specific repair notes.
- `reject`: route back to final-export repair or earlier motion/final packaging as named by the reviewer.
