# Long-Form Audio Timing Provenance - Piltdown Man Voiceover Repair

Date: 2026-05-18

## Disposition

`pass_for_audio_review`

The Piltdown Man long-form WAV was rerendered from the approved voiceover-repaired script revision. Timing sidecars exist for review and future alignment work. Future visible Living Cover captions remain script-locked; ASR text may supply timing evidence only.

## Audio Package

- Pipeline: `ep6_piltdownman_production`
- Pipeline directory: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production`
- Audio package: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/audio_package.json`
- Audio package SHA-256: `192fde6f841cd3f4ee228c95fd8c4fb5a67129619a12a58f298003d26d28e7c9`
- Packaged WAV: `/Users/mike/Episodes_CascadeEffects/Ep6_Piltdown-Man/final/Ep6_Piltdown-Man.wav`
- Packaged WAV SHA-256: `fa215461f2e522816d462d2bbfe9a85c607efecd002999d5e5c8a8e4df91e127`
- Provider: `elevenlabs`
- Model: `eleven_multilingual_v2`
- Voice: `dPrTCMw2R7HQlznlgwCO`
- Voice profile: `longform_mike_v1`
- Packaged at: `2026-05-18T22:55:07Z`
- QA completed at: `2026-05-18T22:57:49Z`

## Media Probe

- Format: `wav`
- Codec: `pcm_s16le`
- Sample format: `s16`
- Sample rate: `44100`
- Channels: `1`
- Duration: `840.980317` seconds
- Runtime: `14:00.980`
- Size: `74174542` bytes
- Bit rate: `705600`

## Render Manifest

- Final jobs: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/final_jobs_voiceover_repair_20260518.jsonl`
- Final jobs SHA-256: `e6e6acd0f319f44460e2e238da40a3d0749b96712776e5e95566f110cd7649aa`
- Effective ElevenLabs manifest: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/effective_final_jobs.elevenlabs.jsonl`
- Effective manifest SHA-256: `cc22cba6c2a92f1ac5a254e0ca6dc3ac1e0785a220433534a5a061f704484520`
- Effective manifest copy: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/effective_final_jobs_voiceover_repair_20260518.elevenlabs.jsonl`
- Effective manifest copy SHA-256: `cc22cba6c2a92f1ac5a254e0ca6dc3ac1e0785a220433534a5a061f704484520`
- Strict source alignment: `pass`
- Spoken input matches locked script after normalization: `pass`
- Normalized script tokens: `1928`
- Normalized spoken-input tokens: `1928`
- Pronunciation preflight: `pass`, `jobs=5`, `matched=0`, `blockers=0`

## Transcription And Timing Sidecars

- Transcript TXT: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/transcripts_mastered_voiceover_repair_20260518/Ep6_Piltdown-Man.diarized.txt`
- Transcript TXT SHA-256: `93543984e1ea20f7a65c48a13af642e5e51052487d3d24104d15337fdc0cba4a`
- SRT timing sidecar: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/transcripts_mastered_voiceover_repair_20260518/Ep6_Piltdown-Man.diarized.srt`
- SRT SHA-256: `2289a90432340d719164fe8f18158bf641ec97bf20d44e1d062cf89024986b6f`
- VTT timing sidecar: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/transcripts_mastered_voiceover_repair_20260518/Ep6_Piltdown-Man.diarized.vtt`
- VTT SHA-256: `8b5a4ed0ba14f65aef93de861406c5352e64ee7078c219ac808dece76584d6b0`
- WhisperX JSON: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/transcripts_mastered_voiceover_repair_20260518/Ep6_Piltdown-Man.whisperx.json`
- WhisperX JSON SHA-256: `96bbc088191a76244d81592efca27cbbf57128817b2cf1a0b62fa76f91efb514`
- WhisperX log: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/transcripts_mastered_voiceover_repair_20260518/logs/transcribe.20260518-155507.log`

## Repair Read

- Formal phrase `British Museum (Natural History)` in revised script and render manifests: `0`
- Formal phrase in new ASR transcript: `0`
- ASR first-line read: `In December 1912, the London Museum we now call the Natural History Museum announced the discovery of a remarkable fossil.`
- This is an ASR check only; visible caption text remains locked to the revised script.

## Guard And Mastering

- Prosody guard report: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/prosody_guard_voiceover_repair_20260518/guard_report.json`
- Prosody guard SHA-256: `6f57e627a972657c43102df0d15c215e3f6cb48b96f97ba2fd9fdb32a7d307fc`
- Prosody guard result: `ok_no_repairs`
- Mastering loudnorm scan: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/mastering_voiceover_repair_20260518/loudnorm_scan.json`
- Mastering loudnorm scan SHA-256: `ad7282fd5fef599e6027892c2fa85a123761b9a1eaf1d3efafdca55ceac1336f`
- Mastering second-pass settings: `/Users/mike/Audio_CascadeEffects/tmp/ep6_piltdownman_production/mastering_voiceover_repair_20260518/loudnorm_second_pass.json`
- Mastering second-pass SHA-256: `b6c64d29728ded8982b97f120dbf79370a822a2e03eab90ea94af1d03c8fc892`

## Caption Policy

- Caption timing provenance exists: `pass`
- Visible future caption source: locked narration script only
- ASR text as visible caption source: `blocked`
- Rough assembly caption gate still requires script-locked caption generation and alignment coverage review.
