---
name: "youtube_shorts_audio_elevenlabs_v1"
description: "Produce Cascade Effects YouTube Shorts audio packages with WAV, QA transcript, provenance, and caption-source handoff."
---

# YouTube Shorts Audio ElevenLabs v1

Use this skill only for the `audio` stage of Cascade Effects YouTube Shorts production with the existing ElevenLabs pipeline.

This is the active short-form audio workflow. It is not the long-form podcast workflow and it does not own stills, motion, proofs, captions, or final export.

Related coordinator skill:

- [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md)

Canonical coordinator flow:

`script -> audio -> stills contact sheet -> stills video proof -> motion contact sheet -> motion video proof -> video final`

## Outcome Contract

This skill produces a promotable short-specific audio package:

- short-specific packaged WAV
- short-specific QA transcript
- `audio_package.json` with provider, model, voice, named voice profile, package hashes, transcript hashes, and profile settings provenance
- caption-source handoff to the Shorts coordinator and final-export skill
- isolated short lane outputs that do not replace long-form episode audio by default

This skill does not treat the following as promotable:

- compile-only manifests
- costing manifests
- hotspot audition clips
- alternate comparison clips
- draft renders without both `merge` and `qa`
- audio lacking a QA transcript or provenance

This skill does not produce stills, motion, contact sheets, video proofs, caption overlays, or video finals.

## Shared Vocabulary

- `keep`
- `tighten`
- `diagnostic only`
- `reject`

## Required Inputs

- `episode_id`
- `short_id`
- short-specific script path
- short-specific pipeline directory
- applicable voice profile or explicit voice settings
- ElevenLabs credentials and configured default model

## Source-Of-Truth Rules

- The source text must be a short-specific script, not the long-form episode script.
- The package must stay in an isolated short lane.
- The short package must not replace the long-form episode package unless explicitly requested.
- If the short is experimental, alternate, or comparison-only, keep it isolated and unpromoted.
- If the short script changes, rerun the short package instead of reusing stale QA output.
- The named Shorts voice profile registry is [/Users/mike/Audio_CascadeEffects/references/voice_profiles/youtube_shorts_voice_profiles.json](/Users/mike/Audio_CascadeEffects/references/voice_profiles/youtube_shorts_voice_profiles.json).
- The default active Shorts profile is `youtube_shorts_mike_challenger_match_v1`; `youtube_shorts_mike_eleven_v3_experiment` is comparison/diagnostic only, even when it uses the same ElevenLabs voice ID.
- `audio_package.json` must include or support validation of `voice_profile_id`, provider, voice ID, model, effective manifest, packaged WAV hash, transcript hash, and render settings such as speed when available.
- Long-form audio packages are cataloged separately and must never be silently reused as short audio.

## Workflow

1. Start from the short-specific script.
Do not render reviewable short audio from the long-form script by default.

2. Render in an isolated short pipeline.
Use a short-specific pipeline directory and short-specific output paths.

3. Require `merge`.
`merge` must create the packaged short WAV and initialize `audio_package.json`.

4. Require `qa`.
`qa` must create the short transcript and update `audio_package.json`.

5. Verify provenance.
Before treating the package as reviewable, confirm `audio_package.json` records the short WAV path, transcript path, provider, model, voice provenance, voice profile, render settings provenance, and package timing.

6. Decide disposition.
Only merged plus QA-complete packages with matching provenance can be `keep`.

7. Hand off to Shorts production.
Provide the short WAV path, transcript path, audio package path, disposition, and caption-source status to the YouTube Shorts coordinator.

## Handoff Packet

Return:

```yaml
stage: audio
episode_id:
short_id:
inputs_used:
artifacts_created:
short_audio_package_path:
short_audio_wav_path:
short_audio_transcript_path:
caption_source_path:
audio_package_sha256:
packaged_audio_sha256:
transcript_sha256:
transcript_or_caption_source:
provider:
model:
voice_id:
voice_profile_id:
voice_profile_registry_path:
disposition: keep | tighten | diagnostic only | reject
blockers:
next_action:
may_advance: false
```

The coordinator decides whether the visual stages may advance.

## Review Rules

- Only a merged plus QA-complete short package may be `keep`.
- Compile-only artifacts, draft renders, and hotspot comparison clips are `diagnostic only`.
- If the transcript is missing after render, the package is at best `tighten`.
- If provenance is missing or mismatched, disposition is `reject`.
- If provider, voice ID, model, or render settings do not match the expected named profile, disposition is `reject` for active Shorts.
- If a package uses the same Mike voice ID with `eleven_v3`, classify it as `diagnostic only` unless the coordinator has explicitly promoted a new active profile.
- If the transcript is stale relative to the short script, rerun audio QA before handoff.

## Required Artifact

- [templates/short_audio_package_review_checklist.md](templates/short_audio_package_review_checklist.md)

## Worked Example

Use Challenger as the primary worked example:

- short script: [/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/challenger_short_v3_trimmed.txt](/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/challenger_short_v3_trimmed.txt)
- packaged short WAV: [/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/final/challenger_short_v3_trimmed.wav](/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/final/challenger_short_v3_trimmed.wav)

Expected output is a `keep` audio handoff packet with WAV, QA transcript, `audio_package.json`, and `transcript_or_caption_source`.

## Edge Cases

- If the short audio is a comparison lane, do not promote it into a canonical episode-owned review asset by default.
- If the short reuses the same brand voice as a long-form package, keep the package isolated anyway.
- If the coordinator asks for captions and the transcript is missing or stale, route back through this skill before final export.
- If the user asks for final captions, hand off the transcript source; do not create visual caption overlays here.
