# Shorts Caption And Final-Export Policy

Use this reference with `youtube_shorts_production_v1/SKILL.md` when routing `video final` to the final-export skill or deciding whether caption/text changes reset earlier stages.

## Generated Visual Text Policy

- During the Challenger-first restart, generated visual text/logo/UI/poster controls are inactive legacy defaults unless the active episode constraint ledger approves the current scoped rule.
- When the active ledger includes a no-text/no-logo visual constraint, text leakage in generated visuals remains a defect even though final captions are allowed.
- Visual research packets are constraint artifacts only; do not treat reference images, logos, archival document text, or artist style names as prompt targets to copy.

## Final Caption Policy

- YouTube Shorts-style captions are applied only in `video final`.
- Captions use `script_locked_canonical_text_timing_from_asr_v1`: visible/player words are derived from the locked short script or an already script-locked caption output.
- WhisperX, ASR, `.diarized.*`, VTT, and SRT files are timing/alignment evidence only and are blocked as caption word sources unless the artifact is already script-locked with passing QA.
- Required handoff fields are `caption_text_source_path`, `caption_timing_source_path`, `caption_text_source_policy`, `caption_timing_source_policy`, `caption_text_matches_script_read`, and `caption_asr_text_not_used_read`.
- Burned-in caption text and uploaded/player sidecar caption text must derive from the same script-locked source.
- Default caption style preset: `minimal_surreal_editorial_v1`.
- Use restrained editorial companion typography: warm off-white bold sans text, soft charcoal edge/shadow, no hard black TV-caption boxes, no bouncing, no karaoke timing, no meme styling, and no coverage of the mechanism, faces, or key anomaly.
- Keep `documentary_lower_third_v1` as a legacy fallback for diagnostic exports or cases where the default preset fails legibility QA.

## Motif Outro Mix Policy

- Final music beds, loops, and theme outros are final-export finishing layers, not ElevenLabs audio-stage renders.
- Active Shorts default to `music_policy: canonical_default` and `music_track_id: paper_architecture_theme_v1` from `/Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json`, unless the coordinator records a waiver or registry-backed alternate.
- The Signature Consequence Motif remains the semantic close. Music should make the ending feel inevitable, not compete with the words.
- The body loop should sit under narration. The outro may enter quietly before the motif ends, then ramp after the final motif word resolves.
- If the outro feels cut off, start with a short final-frame hold of about `0.5-0.75` seconds rather than compressing the music ramp into the existing picture duration. When the registered track's `outro_completion_policy` requires completion, extend the visual duration long enough for the outro to finish; if that creates a visible freeze, use approved no-audio continuation footage as `source_motion_tail` when available.
- The final manifest must record `music_track_registry_path`, `music_track_id`, `music_policy`, `music_rights_check_status`, loop/outro source paths and hashes, timing, volume/ramp values, visual extension mode, final-frame hold duration, source tail path/span when used, residual cloned hold, outro duration used, cutoff seconds, final mix peak level, `motif_music_bed_read`, and `outro_completion_read`.
- Reject or tighten any mix that masks the motif, makes the motif cadence feel unresolved, clips, starts the outro as a competing second ending, or cuts off the outro tail.

## Final-Export Handoff

Route final assembly to [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_final_export_v1/SKILL.md) only after an approved `motion video proof`.

The final-export request must include:

- approved motion proof path
- approved audio path and audio package path
- script-locked `caption_text_source_path`
- ASR/WhisperX `caption_timing_source_path`
- proof review note path
- caption style preset
- caption placement or placement constraints
- expected voice profile and audio package hash
- transcript hash for audio package provenance
- any manual timing adjustments or known caption risks
- canonical, waived, or alternate music policy fields plus any approved final music bed, body loop, theme outro, or final-frame hold instructions

The final manifest records `caption_text_source_path`, `caption_timing_source_path`, `caption_text_matches_script_read`, `caption_asr_text_not_used_read`, `caption_style_preset`, `caption_placement`, `caption_timing_path`, `captioned_final_path`, manual timing adjustments, music policy fields, and any `motif_outro_mix` fields.

Caption changes reset only `video final` unless they reveal timing problems in the motion proof.
