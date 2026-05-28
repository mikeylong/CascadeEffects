---
name: "youtube_shorts_final_export_v1"
description: "Create Cascade Effects YouTube Shorts video finals with script-locked caption overlays from approved motion proofs and audio."
---

# YouTube Shorts Final Export v1

Use this skill only for the `video final` stage of Cascade Effects YouTube Shorts production.

This skill is a specialist reference called by the active coordinator:

- [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md)

It does not own script, audio, visual research packet, stills contact sheet, stills video proof, motion contact sheet, motion video proof, or local first-second hook review sets. It starts only after the coordinator has approved the `motion video proof` gate and, when a first-second hook retrofit is in scope, after the local hook review has a human `keep`.

## Outcome Contract

This skill produces:

- a caption timing file or caption overlay manifest
- a mandatory house CRT plus Challenger-style signal-interruption motion-only rebuild manifest, unless the coordinator records an explicit waiver
- a YouTube Shorts-style captioned vertical final MP4
- a final export manifest
- a final QA/review note
- a handoff packet back to the Shorts coordinator
- a default `motif_outro_mix` using the Shorts music registry's `paper_architecture_theme_v1`, unless the coordinator records waived or alternate-approved music policy
- an approved first-second hook rebuild only when the coordinator supplies human-kept `first_second_hook_context`
- a handoff to the publish skill when a keeper final/package is built

This skill does not produce:

- script revisions
- audio rerenders
- still candidates
- motion candidates
- contact sheets
- mixed-review proof cuts
- local first-second hook review packages
- unlisted review uploads, status checks, deletes, or public release actions
- publishable output from non-`keep` motion

## Required Inputs

- `episode_id`, `short_id`, and output target directory
- approved `motion video proof` path and manifest path
- approved short audio WAV path, package path, expected voice profile ID, audio package hash, packaged audio hash, transcript hash, and `keep` audio disposition
- Signature Consequence Motif fields: `brand_motif_status`, `motif_family` when applicable, `motif_text`, `motif_waiver_reason` when applicable, and `ending_cadence_read`
- `caption_text_source_path`: locked short script text or an already script-locked caption source with passing QA
- `caption_timing_source_path`: ASR/WhisperX/SRT/VTT/JSON timing evidence; this may come from the approved audio package transcript/timing, but its words are timing-only
- motion proof review note path
- final caption style preset, defaulting to `minimal_surreal_editorial_v1`
- final-gate house CRT plus Challenger-style signal-interruption manifest from the approved no-caption motion proof, or an explicit coordinator waiver reason
- final music policy instructions: `music_track_registry_path`, `music_track_id`, `music_policy: canonical_default|waived|alternate_approved`, `music_waiver_reason`, `music_rights_check_status`, `motif_outro_mix_used`, body loop path/hash, outro path/hash, start/end times, volume/ramp values, any allowed final-frame hold duration, and any approved no-audio `source_motion_tail` used to avoid cloned-frame visual padding
- first-second hook inputs when in scope: `first_second_hook_manifest_path`, `first_second_hook_read: pass`, `human_review_disposition: keep`, `cold_flash_prebeat_context`, `opening_impact_audio_context`, `current_latest_publish_mp4_path`, and duration-trim instructions

## Final Gate

Before exporting, verify:

- the motion proof disposition is `keep` and the reel class is `keeper short`
- every included motion clip is `keep` and no diagnostic placeholders remain
- the approved audio WAV exists and matches the short audio package `packaged_path`
- the expected voice profile is final-export eligible and audio disposition is `keep`
- the approved audio package and proof manifest record `ending_cadence_read: pass` and a valid Signature Consequence Motif status; missing or question-like motif cadence blocks final export
- package and transcript hashes match the proof manifest for audio provenance; transcript text is not a caption word source
- the caption model is `script_locked_canonical_text_timing_from_asr_v1`
- `caption_text_source_path` exists, is script-locked, and is not `.diarized.*`, WhisperX, raw ASR, VTT, or SRT timing text unless it is already a script-locked output with passing QA
- `caption_timing_source_path` exists and is recorded as ASR/WhisperX timing-only evidence
- `caption_text_matches_script_read`, `caption_asr_text_not_used_read`, and `caption_alignment_coverage_read` are `pass`
- burned-in captions and YouTube/player sidecars derive from the same script-locked caption source
- proof review note and caption style preset exist
- active Shorts have passed the global final-gate contract before captions: require `house_crt_contract_id: house_crt_luma_neutral_chroma_signal_interruption_v1`, `source_lineage_read.clean_source_confirmed: true`, `house_crt_texture_read.profile_id: era_1980s_broadcast_crt_v1`, `house_crt_texture_read.intensity: visible_but_premium`, `texture_tone_policy: luma_neutral_chroma_visible_scanline_v1`, `calibration_recipe_id: premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1`, `scanline_policy_id: luma_neutral_visible_scanline_modulation_v1`, `scanline_strength_variant_id: max_visible_bars_y24_p8`, `scanline_delta_y: 24.0`, `scanline_period_pixels: 8`, `scanline_band_pixels: 2`, `luma_chroma_metrics_read.overall_read: pass`, `signal_interruption_read.profile_id: era_1980s_horizontal_signal_interruption_v2_randomized`, `signal_interruption_read.duration_seconds: 0.25`, `signal_interruption_read.timing_policy: replace_outgoing_segment_tail_preserve_total_duration`, and `signal_interruption_read.full_frame_static_replacement_used: false`, unless the coordinator records an explicit waiver
- active Shorts must record `visual_layer_order_read.caption_burn_is_last_visual_operation: true`, `post_caption_visual_effects_applied: false`, and `motion_source_contains_captions: false`; no CRT, noise, signal interruption, tail texture, comparison, or other visual effect may run after caption burn
- if an earlier proof/motion package also records house CRT signal texture, preserve its provenance fields, but do not treat old era-specific or period-specific archival texture profiles as final-export eligible active policy
- music policy is resolved: canonical default uses `music_track_id: paper_architecture_theme_v1`; waived music has a non-empty `music_waiver_reason`; alternate-approved music has a registry-backed `music_track_id` and source hashes
- if `motif_outro_mix_used: true`, the body loop supports the voiceover, the outro does not compete with the final motif, the audible outro ramp begins after the motif resolves, the outro is not cut off, and the final mix does not clip
- if a first-second hook retrofit is in scope, the local review set has `first_second_hook_read: pass`, `human_review_disposition: keep`, impact audio starts at `t=0.00`, the prebeat is scene-led or event-led, final captions remain the last visual layer, and any duration repair trims nonessential visual hold or tail time instead of the spoken motif, voice cadence, or required caption content
- unresolved mixed-review blockers are absent

If any check fails, return `tighten`, `diagnostic only`, or `reject`; do not create a publishable final.

## Motif Outro Mix Rules

- Treat the spoken Signature Consequence Motif as the semantic ending. The music is a handoff and emotional resolution layer, not a replacement close.
- Active Shorts default to `music_policy: canonical_default`, `music_track_registry_path: /Users/mike/Agents_CascadeEffects/references/shorts/music_track_registry.json`, and `music_track_id: paper_architecture_theme_v1`.
- Apply music only after approved voice/caption timing is locked. Do not reopen ElevenLabs audio for a bed/outro-only change.
- If music is waived, record `music_policy: waived`, `motif_outro_mix_used: false`, and a non-empty `music_waiver_reason`; if an alternate is approved, record `music_policy: alternate_approved`, a registry-backed `music_track_id`, and source hashes.
- The body loop should sit under narration and fade into the outro handoff.
- The outro may begin quietly before the final motif finishes, but it must not draw attention away from the word that resolves the motif.
- Start the audible outro ramp after the motif resolves. Record the ramp start/end times and volume values.
- Start with a `0.5-0.75s` final-frame hold for normal resolution, but if the registered track's `outro_completion_policy` requires it, extend the visual duration long enough for the outro to finish. If the hold is visibly static and clean approved continuation footage exists, use a no-audio `source_motion_tail` instead of cloned-frame padding. Record the required hold, actual hold, visual extension mode, source tail path/span, residual cloned hold, outro duration used, cutoff seconds, and policy in the final manifest.
- The final mix must record `music_track_id`, `music_policy`, `music_rights_check_status`, loop/outro source hashes, `motif_music_bed_read: pass|tighten|reject`, `outro_completion_read: pass|tighten|reject`, and `final_mix_peak_db`. Clipping, masking the motif, question-like ending feel, or a cut-off outro blocks `keep`.

## Caption Rules

- Captions are the last visual layer. Apply every house CRT, signal interruption, tail visual, texture, and comparison-render operation to the no-caption motion bed first; after caption burn, only stream-only audio muxing is allowed.
- Generated stills and motion must remain free of baked-in captions, readable text, UI overlays, logos, and poster graphics.
- Text leakage in generated visuals remains a visual defect, even when the final has approved captions.
- Caption model is `script_locked_canonical_text_timing_from_asr_v1`: caption words come from the locked short script or an already script-locked caption source; ASR/WhisperX/SRT/VTT/JSON evidence supplies timing only.
- The approved audio package transcript may be used to verify timing/alignment and audio provenance, but it is blocked as a caption word source unless it is already a script-locked output with passing QA.
- Public burned-in captions and YouTube/player sidecars must share the same script-locked text source. If they differ, block publish readiness.
- `.diarized.*`, WhisperX, raw ASR, VTT, and SRT timing files are blocked as caption text sources by default because ASR can mishear proper nouns, technical terms, and short motif wording.
- Final caption artifacts must record `caption_text_source_path`, `caption_timing_source_path`, `caption_text_source_policy`, `caption_timing_source_policy`, `caption_text_matches_script_read`, `caption_asr_text_not_used_read`, and `burned_in_and_sidecar_same_script_locked_source_read`.
- The final caption sequence must preserve the approved spoken motif exactly as transcribed. If the caption layer drops, rewrites, or retimes the closing motif in a way that weakens the terminal read, route back to `video final`; if the audio delivery itself fails cadence, route back to `audio`.
- Default style preset: `minimal_surreal_editorial_v1`; 1910s newspaper/steamship-era preset: `era_1910s_newspaper_ivory_v1`; 1940s archival-film preset: `era_1940s_newsreel_ivory_v1`; early-1980s broadcast character-generator preset: `early_1980s_broadcast_cg_v1`; legacy fallback preset: `documentary_lower_third_v1` for diagnostic exports or cases where the minimal-surreal preset fails legibility QA.
- Use phrase-level captions, not karaoke word-by-word timing.
- Keep captions to 1-2 lines in a mobile-safe lower third.
- Default to lower-center placement, but use a recorded placement override such as `lower-left` when lower-center covers the mechanism, faces, key anomaly, or crucial motion.
- Use restrained editorial companion typography. For modern minimal-surreal finals, use a saturated semantic accent color with a soft charcoal edge/shadow and no hard black TV-caption box. For Titanic/1910s finals, use `era_1910s_newspaper_ivory_v1`: Baskerville-style period serif, warm ivory text, and a soft sepia-charcoal edge; avoid 1940s newsreel Futura, fake silent-film title cards, and modern amber captions. For 1940s archival-film finals, use `era_1940s_newsreel_ivory_v1`: Futura Condensed ExtraBold period sans, warm ivory text, and a soft sepia-charcoal edge. For 1981 broadcast-linked finals, prefer `early_1980s_broadcast_cg_v1`: hard-edged mono/CG typography, pale phosphor/cyan-white text, and a deep broadcast-blue edge; do not add Amiga desktop windows, icons, menus, date stamps, or fake terminal chrome unless explicitly approved.
- At 1080x1920, use roughly 78-88 px text with a maximum text width around 860 px.
- Prefer short chunks, usually 1.2-2.4 seconds, split on spoken phrase boundaries.
- Avoid karaoke word-by-word timing, emoji, bouncing, meme styling, poster graphics, and all-caps except source emphasis.
- Captions must not cover the mechanism, faces, key anomaly, or crucial motion.
- Manual timing adjustments and placement overrides must be recorded in the final export manifest.

## Workflow

1. Load the final-export request.
Confirm the coordinator supplied approved motion proof, audio, script-locked caption text source, timing evidence, proof review, and caption preset.

2. Prepare caption timing.
Create or verify phrase-level caption timing by aligning locked script words to ASR/WhisperX timing evidence. Do not copy ASR words into the output captions.

3. Apply any human-kept first-second hook rebuild.
When the coordinator supplies approved hook context, prepend the `0.75s` cold-flash prebeat to the no-caption picture bed before caption timing is offset. Do not use local-review proof excerpts as finals. Confirm the opening impact hit starts at `t=0.00`; record the source asset hash and duration-trim decision.

4. Apply the house CRT/signal-interruption final gate.
Before captions, rebuild the approved no-caption motion proof into a no-audio picture bed using the global `house_crt_luma_neutral_chroma_signal_interruption_v1` contract with selected visible CRT scanlines (`max_visible_bars_y24_p8`) and Challenger-style randomized signal interruption at eligible story-clip cuts. The source-lineage gate must first reject pre-textured proofs or segment sources and record `source_lineage_read.clean_source_confirmed: true`. The interruption mutates the outgoing footage's final `0.25s` with horizontal analog signal breaks; it is not a full-frame static card. Captions, logos, lower-thirds, and audio must not be present in this motion-only intermediate. The first-eight batch command is:

```bash
python3 /Users/mike/Viz_CascadeEffects/scripts/house_crt_static_final_pass.py --visible-scanline-first-eight-final-set
```

For later Shorts that have current final/proof provenance in episode TOML, use `--visible-scanline-final-gate --current-final-set`; for a custom final source, use `--visible-scanline-final-gate --final-manifest <final-export-manifest>`. The resulting final-gate manifest is then supplied to final export with `--house-crt-final-gate-manifest` or the backward-compatible `--house-crt-static-manifest`.

5. Apply caption overlays.
Burn or composite Shorts-style captions onto the house CRT/signal-interruption no-audio picture bed while preserving approved timing.

5a. Apply optional motif/outro mix.
If the coordinator supplied `motif_outro_mix` instructions, mix the approved voice audio with the body loop and outro after captions are applied or while preserving identical caption timing. Record any final-frame hold explicitly. If a long visual extension would freeze, pass an approved no-audio 9:16 `source_motion_tail` into final export and keep residual cloned-frame hold at or below the recorded threshold.

For already-approved keeper proofs, prefer the shorter wrapper:

```bash
/Users/mike/Viz_CascadeEffects/bin/ce short final-approved <proof-manifest-or-build-dir> \
  --proof-review-note <approved-motion-proof-review-note> \
  --caption-style minimal_surreal_editorial_v1
```

Use `bin/ce short final-export` when every gate assertion must be explicit in the command line.

6. Run final QA.
Check vertical aspect, audio sync, first-second hook timing when used, caption legibility, caption safe zone, no mechanism occlusion, no placeholders, and final duration.

7. Write final artifacts.
Record the house CRT/signal-interruption manifest, caption timing path, caption overlay manifest, captioned final MP4, final export manifest, and final review note.

8. Hand off to the coordinator.
Return a stage packet with `stage: video final`, final paths, disposition, blockers, and `may_advance: false` for any remaining issue. When the final is `keep` and a publish package exists, set the next action to route the package to [/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md](/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_publish_v1/SKILL.md) for `publish-package-check`, `publish-package-upload --privacy unlisted`, status receipts, and Studio-check guidance. Do not upload from this final-export skill.

## Output Format

Use:

- [templates/final_export_request_template.md](templates/final_export_request_template.md)
- [templates/caption_overlay_manifest_template.md](templates/caption_overlay_manifest_template.md)
- [templates/final_export_review_template.md](templates/final_export_review_template.md)
- [examples/challenger_final_export_request_minimal_surreal_v1.md](examples/challenger_final_export_request_minimal_surreal_v1.md) as the canonical filled-in request example

The handoff packet must include:

```yaml
stage: video final
episode_id:
short_id:
inputs_used:
artifacts_created:
approved_inputs: [proof_video_path, review_note_path, caption_text_source_path, caption_timing_source_path]
audio_context: [short_audio_package_path, brand_motif_status, motif_family, motif_text, ending_cadence_read]
final_music_context: [music_track_registry_path, music_track_id, music_policy, music_waiver_reason, music_rights_check_status, motif_outro_mix_used, body_loop_path, body_loop_sha256, outro_path, outro_sha256, visual_extension_mode, final_frame_hold_seconds, source_motion_tail_path, source_motion_tail_source_clip_id, source_motion_tail_source_span_in, source_motion_tail_source_span_out, source_motion_tail_residual_hold_seconds, motif_music_bed_read, outro_completion_read, final_mix_peak_db]
first_second_hook_context: [first_second_hook_manifest_path, first_second_hook_read, human_review_disposition, cold_flash_prebeat_context, opening_impact_audio_context, first_second_hook_applied, caption_offset_seconds, duration_trim_decision]
house_crt_static_context: [house_crt_static_manifest_path, house_crt_static_status, house_crt_texture_read, signal_interruption_read, final_picture_source_path]
caption_context: [caption_model, caption_text_source_path, caption_timing_source_path, caption_text_matches_script_read, caption_asr_text_not_used_read, caption_style_preset, caption_placement, caption_timing_path]
final_outputs: [caption_overlay_manifest_path, captioned_final_path, final_export_manifest_path]
publish_handoff: [publish_package_manifest_path, publish_package_check_command, publish_skill_path, public_release_boundary]
disposition: keep | tighten | diagnostic only | reject
reel_class: keeper short | mixed review short
blockers:
next_action:
may_advance: true | false
```

Only the coordinator may treat `may_advance: true` as production advancement.

## Edge Cases

- If locked script caption text is missing, route back to script/audio handoff; do not use ASR words as a fallback and do not invent captions from memory.
- If caption timing reveals proof-level audio sync problems, route back to `motion video proof`.
- If captions cover the mechanism or anomaly, adjust caption placement before export.
- If the motion proof is `mixed review short`, reject final export and return blockers to the coordinator.
- If the user asks for caption styling only, revise final-export artifacts without reopening script, audio, stills, or motion unless timing defects are discovered.
- If first-second hook context exists but lacks human `keep`, do not apply the hook in final export; return to the coordinator with `diagnostic only` or `tighten`.

## Example

Request:

> Make the final with captions for `hyatt_short_minimal_surreal_v3_story_stills_v2`.

Expected behavior:

- confirm the motion proof is approved as `keeper short`
- use the approved short audio plus locked script text
- create phrase-level caption timing from ASR timing evidence without using ASR words
- export a captioned vertical MP4
- record script-locked caption text source, timing source, style preset, timing path, final path, and QA note
- return `reject` or `tighten` instead of finalizing if the proof is still mixed review
