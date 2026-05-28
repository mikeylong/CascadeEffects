# 737 MAX Long-Form Audio Source Integrity

- episode: 737 MAX
- workflow: long_form_video_production_v1
- recorded_at_utc: 2026-05-18T22:50:50Z
- disposition: review_ready_pending_human_audio_keep
- may_mark_audio_keep: false
- may_advance_to_visual_system: false
- may_youtube_action: false

## Gate Reads

- frontier_model_script_critique_read: pass_with_tightening
- critique_integration_read: pass_required_change_integrated
- human_script_approval_for_audio_read: pass
- audio_render_read: pass
- audio_source_integrity_read: pass
- caption_timing_source_read: pass
- full_decode_read: pass
- audio_review_keep_read: pending_human_listen

## Render Contract

- approved_script_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/Ep7_737-MAX.txt
- approved_script_sha256: 3f95aaf72b3144f0c33ee85e77d18140a888ba97c46eb89b0cfaad5c61a7c718
- render_alignment_script_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/audio_render_script_cue_normalized_20260518.txt
- render_alignment_script_sha256: 58f46909572ebc3318ce3fa7c39896a2c97a383d6ca580813437f58b1be6d029
- render_alignment_script_read: pass_spoken_text_identical_after_tag_strip
- human_script_approval_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/human_script_approval_for_audio_20260518.md
- human_script_approval_sha256: 6f6e8c4cc137fd7c517179743117d054f5080651c13d1f23a6d782f4ff889977
- final_jobs_path: /Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/final_jobs.jsonl
- final_jobs_sha256: b8ccd39b6a814097c6efaa89c3679e233437fe0f65384ee082662642f5395458
- effective_final_jobs_path: /Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/effective_final_jobs.elevenlabs.jsonl
- effective_final_jobs_sha256: 39ff725c54d922db72638a404a119fe737158e221af9f54194a736055fab6045
- provider: ElevenLabs
- voice_profile_id: longform_mike_v1
- voice_id: dPrTCMw2R7HQlznlgwCO
- model: eleven_multilingual_v2
- speed: 0.95

## Promoted Audio

- wav_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/final/Ep7_737-MAX.wav
- wav_sha256: adaf19d653f7d673d601ba0f273ef822dbce375dee25ec5c3554f687b839db71
- duration_seconds: 942.869478
- codec: pcm_s16le
- sample_rate: 44100
- channels: 1
- bits_per_sample: 16
- ffprobe_json_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/qa/Ep7_737-MAX_ffprobe_20260518.json
- ffprobe_json_sha256: 9e85aa9b5dc6c53109ded505eec50abda54f35e497c4cde4bcb10af628d857ef
- full_decode_log_path: /Users/mike/Episodes_CascadeEffects/Ep7_737-MAX/production/long_form_video_v1/qa/Ep7_737-MAX_full_decode_20260518.log
- full_decode_log_sha256: e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855

## Audio Package And QA

- audio_package_path: /Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/audio_package.json
- audio_package_sha256: 7fccfc02233388dc0a31a85443f7a40fe611e79eb2968883978c1c444aa416b6
- packaged_at: 2026-05-18T22:47:30Z
- qa_completed_at: 2026-05-18T22:50:37Z
- qa_transcript_txt_path: /Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.diarized.txt
- qa_transcript_txt_sha256: 19e46f58fb0e6daceb58af1b58db20ca60b1d47305fe70778a12191bc49e3633
- qa_transcript_srt_path: /Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.diarized.srt
- qa_transcript_srt_sha256: d0ea85324c5b7aa07e290ba9f468a1dc26a70c4686ef5f59d26b8ea33e188096
- qa_transcript_vtt_path: /Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.diarized.vtt
- qa_transcript_vtt_sha256: f45906753a5660d6744060d0281b615b29297cae5aa80b5acca85a2baf2c83c5
- whisperx_json_path: /Users/mike/Audio_CascadeEffects/tmp/transcripts_final/Ep7_737-MAX.whisperx.json
- whisperx_json_sha256: 6b2cd28bd172c0fff59c113b1b465fc0853cf57a7af0a529590d80ea5747ae8f
- prosody_guard_report_path: /Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/prosody_guard/guard_report.json
- prosody_guard_report_sha256: 6f57e627a972657c43102df0d15c215e3f6cb48b96f97ba2fd9fdb32a7d307fc
- loudnorm_scan_path: /Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/mastering/loudnorm_scan.json
- loudnorm_scan_sha256: b6cafa974274dab2c3516289586b0ccf96acf394cfd27319ea4ffc4a02438297
- loudnorm_second_pass_path: /Users/mike/Audio_CascadeEffects/tmp/ep7_737max_production/mastering/loudnorm_second_pass.json
- loudnorm_second_pass_sha256: dcfa5bc5cdcf3300506d1af25c74d79ed1b9016de3dc9849609868d1c52265b7

## Boundary

The rendered WAV is review-ready for human audio listen/keep only. It does not authorize visual-system planning, rough assembly, upload, visibility changes, or public release.
