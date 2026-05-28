# 737 MAX Long-Form Audio Handoff

Date: 2026-05-18

Workflow: `long_form_video_production_v1`

Gate: `episode_package_keep`

Disposition: `audio_keep_package_review_ready_pending_package_keep`

## Handoff State

The long-form audio render is complete, promoted to the canonical episode final WAV, and marked human audio `keep`. The next gate is episode package review. This handoff does not authorize visual-system planning, rough assembly, upload, visibility changes, or public release until the package gate receives explicit `keep`.

## Approved Source And Render Inputs

- Approved script path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt`
- Approved script SHA-256: `3f95aaf72b3144f0c33ee85e77d18140a888ba97c46eb89b0cfaad5c61a7c718`
- Human script approval path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/human_script_approval_for_audio_20260518.md`
- Human script approval SHA-256: `6f6e8c4cc137fd7c517179743117d054f5080651c13d1f23a6d782f4ff889977`
- Render alignment script path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/audio_render_script_cue_normalized_20260518.txt`
- Render alignment script SHA-256: `58f46909572ebc3318ce3fa7c39896a2c97a383d6ca580813437f58b1be6d029`
- Render alignment script read: `pass_spoken_text_identical_to_approved_script_after_tag_strip`
- Final jobs path: `/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/final_jobs.jsonl`
- Final jobs SHA-256: `b8ccd39b6a814097c6efaa89c3679e233437fe0f65384ee082662642f5395458`
- Effective final jobs path: `/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/effective_final_jobs.elevenlabs.jsonl`
- Effective final jobs SHA-256: `39ff725c54d922db72638a404a119fe737158e221af9f54194a736055fab6045`
- Provider: `elevenlabs`
- Voice profile: `longform_mike_v1`
- Voice: `dPrTCMw2R7HQlznlgwCO`
- Model: `eleven_multilingual_v2`
- Speed: `0.95`

## Promoted Audio And QA

- WAV path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/final/Ep7_737-MAX.wav`
- WAV SHA-256: `adaf19d653f7d673d601ba0f273ef822dbce375dee25ec5c3554f687b839db71`
- Duration seconds: `942.869478`
- Codec: `pcm_s16le`
- Sample rate: `44100`
- Channels: `1`
- Audio package path: `/Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/audio_package.json`
- Audio package SHA-256: `7fccfc02233388dc0a31a85443f7a40fe611e79eb2968883978c1c444aa416b6`
- QA transcript path: `/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.diarized.txt`
- QA transcript SHA-256: `19e46f58fb0e6daceb58af1b58db20ca60b1d47305fe70778a12191bc49e3633`
- SRT path: `/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.diarized.srt`
- SRT SHA-256: `d0ea85324c5b7aa07e290ba9f468a1dc26a70c4686ef5f59d26b8ea33e188096`
- VTT path: `/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.diarized.vtt`
- VTT SHA-256: `f45906753a5660d6744060d0281b615b29297cae5aa80b5acca85a2baf2c83c5`
- WhisperX JSON path: `/Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.whisperx.json`
- WhisperX JSON SHA-256: `6b2cd28bd172c0fff59c113b1b465fc0853cf57a7af0a529590d80ea5747ae8f`
- Source integrity note: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/audio_source_integrity_20260518.md`
- Source integrity note SHA-256: `b45308b79c6221a4b1c08798aff6061ff33c07b85073813edb2b5af46f0d912e`
- Human audio keep path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/human_audio_keep_20260519.md`
- Human audio keep SHA-256: `bb4f697edb02646e862d8019cda97cea7714a63209edaa0ae06c6d4ac7722bc1`
- Episode package gate path: `/Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/episode_package_gate_audio_keep_pending_package_keep_20260519.md`
- Episode package gate SHA-256: `e0cf5c6d62f10a909efb12b53299a8ac0054f2b2461d9ad424d8532e0689fc65`

## Gate Reads

- `frontier_model_script_critique_read`: `pass_with_tightening`
- `critique_integration_read`: `pass_required_change_integrated`
- `human_script_approval_for_audio_read`: `pass`
- `audio_render_read`: `pass`
- `audio_source_integrity_read`: `pass`
- `caption_timing_source_read`: `pass`
- `full_decode_read`: `pass`
- `audio_review_keep_read`: `pass`
- `episode_package_gate_read`: `review_ready_pending_package_keep`
- `may_mark_audio_keep`: `true`
- `may_advance_to_visual_system`: `false`
- `may_youtube_action`: `false`
