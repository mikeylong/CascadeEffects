# Episode Package Gate - Titanic Long-Form

Date: 2026-05-18

## Disposition

`review_ready_pending_human_audio_keep`

The Titanic compact long-form package now has an approved post-critique script, fresh long-form audio, timing provenance, and source-integrity evidence. The package is not `keep` yet. Visual-system planning, source-art generation, rough assembly, final MP4 render, upload prep, and YouTube action remain blocked until Mike reviews the audio and explicitly marks it `keep`, then reviews the episode package gate.

## Canonical Source

- Script path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/Ep8_Titanic.txt`
- Script SHA-256: `38056564c66cb5249d02f37dffaf98c4acdea680465e1d9b93d01d06102e38cc`
- Script word count: `1849`
- Fact-check path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/fact_check.md`
- Fact-check SHA-256: `9fc695539a22737d739f957e34a6a626cc685e349803613808449892effd335f`
- Runtime target: compact 12-15 minute long-form path
- Series-bible mechanism: `legality can hide obsolete safety assumptions`

## Script Gate Reads

- Frontier-model script critique: `pass`
- Critique path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/frontier_model_script_critique_gpt5_20260518.md`
- Critique SHA-256: `aa12bc555195ef4b546505e23d8e2a99905dcda642ee1b4803932f3adec250f5`
- Critique integration: `pass_no_script_changes_required`
- Integration path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/script_gate_integration_note_20260518.md`
- Integration SHA-256: `8fddb08df1a026d5f73a7c4e0d18dd512e9225e1b4e1b522c6467543bfb7d8e8`
- Human script approval for audio: `pass`
- Approval path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/human_script_approval_for_audio_20260518.md`
- Approval SHA-256: `cd25f2e7b22071f167b334a8ecb1733cb8d8b847e6e8d8972262bd99c65e2a53`

## Audio Package Reads

- Audio status: `review_ready_pending_human_keep`
- Packaged WAV: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/final/Ep8_Titanic.wav`
- Packaged WAV SHA-256: `79253cadeae659aa74fcc2b2c32302d0483a9b1be2d6a3e69f97e367b2623a1f`
- Duration: `731.800091` seconds (`12:11.800`)
- Codec: `pcm_s16le`
- Sample rate: `44100`
- Channels: `1`
- Audio package: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_20260518/audio_package.json`
- Audio package SHA-256: `1c9e00939e5d203c17f24b60617963a108f14f0e731c31a9f9a3b4fab0a84825`
- Audio source integrity: `pass`
- Source integrity path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/audio_source_integrity_report_20260518.json`
- Timing provenance: `pass`
- Timing provenance path: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/long_form_audio_timing_provenance_20260518.md`
- Human audio review note: `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/production/long_form_video_v1/human_audio_review_note_20260518.md`

## Timing Sidecars

- Transcript TXT: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_20260518/transcripts_mastered/Ep8_Titanic.diarized.txt`
- Transcript TXT SHA-256: `7ed7ad0f3b63d0045234d2bfd039e85bab049f24ad604a54772ce8cff788c1a7`
- SRT: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_20260518/transcripts_mastered/Ep8_Titanic.diarized.srt`
- SRT SHA-256: `dadde6559955ecf82f12855b12c8ee274808a80ec215e7b2ce821ac911d15145`
- VTT: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_20260518/transcripts_mastered/Ep8_Titanic.diarized.vtt`
- VTT SHA-256: `07d500d9cb571b7023dc60ce618680cfbd32efe983718a974f54f21490d69ebb`
- WhisperX JSON: `/Users/mike/Audio_CascadeEffects/tmp/ep8_titanic_longform_20260518/transcripts_mastered/Ep8_Titanic.whisperx.json`
- WhisperX JSON SHA-256: `9f1d2c13e02b4563578afd9ccdaccce3e397cbed54cfa776c1ca8ba20458a0db`
- Caption text source for future visible captions: locked script only
- ASR text as future visible caption source: `blocked`

## Package Spine

- Opening promise: Titanic had enough lifeboats to satisfy the law.
- Core mechanism: the law measured a tonnage bracket after ship scale had outrun the bracket.
- Cause chain: obsolete lifeboat table, category ceiling, compliance mistaken for sufficiency, optional larger boat capacity, weak evacuation practice, and post-disaster SOLAS correction.
- Consequence: more than 1,500 people died in a system where legal compliance did not equal human-scale escape capacity.
- Closing line: `You already know the disaster. The record shows the mechanism.`

## Short Bridge

- Existing Short bridge status: private review upload processed; manual Studio checks pending.
- Private Short URL: `https://www.youtube.com/watch?v=ufYl87LFBXE`
- Bridge role: discovery/pre-release context only.
- Short audio and Short publish assets are not the long-form source of truth.

## Gate State

- May advance to visual system: `false`
- May start source-art generation: `false`
- May start rough assembly: `false`
- May render final MP4: `false`
- May prepare upload package: `false`
- May perform YouTube action: `false`
- Public release ready: `false`

## Next Required Human Gate

Mike must review `/Users/mike/Episodes_CascadeEffects/Ep8_Titanic/final/Ep8_Titanic.wav` and explicitly record audio `keep` or `tighten`. If the audio earns `keep`, rebuild or update this episode package gate for human package `keep` before any visual-system work begins.
