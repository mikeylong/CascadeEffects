---
name: "youtube_shorts_production_v1"
description: "Coordinate Cascade Effects YouTube Shorts production through script, audio, first-second hook review, visual research, contact-sheet gates, video proofs, and final-export routing."
---

# YouTube Shorts Production v1

Use this skill for active Cascade Effects YouTube Shorts production. It is the coordinator and gatekeeper contract for short-form vertical videos only. During the production restart, Challenger is the only active new visual production target until a DP-approved workflow scope manifest opens another episode.

Canonical production flow:

`fact-checked long-form script -> derived 60-second Short script -> audio -> narration map -> DP scope/research brief -> visual research packet -> production model decision -> visual beatmap -> shot_plan_v2 -> episode constraint ledger -> render authorization check -> motion readiness review -> stills/keyframe contact sheet -> stills video proof when needed -> motion contact sheet -> shot_timing_edl -> motion video proof -> video final -> publish package -> unlisted review upload -> platform checks -> public release decision -> keeper lesson capsule`

When the workflow scope manifest imports archival motion-reference video, keep that top-level flow unchanged but require a DP-owned `archival footage review` inside the `visual research packet` stage before the visual beatmap is locked.

For first-second hook retrofit work on already-built Shorts, treat the local review set as a coordinator-owned diagnostic gate between the latest local publish MP4 inventory and any later final rebuild. Do not upload, delete, replace, schedule, or publish from this retrofit gate.

This skill owns sequence, stage ledger, routing, handoff packets, gate decisions, deferred gaps, and reset calls. Specialist skills and reference docs own stage-specific execution detail.

## Specialist References

- Audio stage: [/Users/mike/CascadeEffects/packages/media-pipeline/audio/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md](/Users/mike/CascadeEffects/packages/media-pipeline/audio/references/skills/youtube_shorts_audio_elevenlabs_v1/SKILL.md)
- Long-form audio script source: [/Users/mike/CascadeEffects/ops/agents/skills/episode_production_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/episode_production_v1/SKILL.md)
- DP scope, research, constraints, and shot planning: [/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/SKILL.md)
- DP research and constraint policy: [/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/references/dp_research_constraint_policy.md](/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/references/dp_research_constraint_policy.md)
- Motion readiness gate for Shorts and long-form: [/Users/mike/CascadeEffects/ops/agents/skills/motion_readiness_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/motion_readiness_v1/SKILL.md)
- Visual style and still/motion judgment: [/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/SKILL.md](/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/SKILL.md)
- House CRT signal texture registry: [/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json](/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json)
- Visual promotion workflow: [/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/judgment/promotion_workflow.md](/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/judgment/promotion_workflow.md)
- Keeper registry, scoped reference only unless DP-imported: [/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/judgment/keeper_registry.md](/Users/mike/CascadeEffects/archive/season-01-reference/legacy-style-packages/style-packages/source_preserving_documentary_v1/judgment/keeper_registry.md)
- Final export stage: [/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_final_export_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_final_export_v1/SKILL.md)
- Publish stage: [/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_publish_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_publish_v1/SKILL.md)
- Cross-episode Shorts audio lane registry: [/Users/mike/CascadeEffects/packages/production-registry/shorts/audio_lane_registry.json](/Users/mike/CascadeEffects/packages/production-registry/shorts/audio_lane_registry.json)
- Canonical Shorts music track registry: [/Users/mike/CascadeEffects/packages/production-registry/shorts/music_track_registry.json](/Users/mike/CascadeEffects/packages/production-registry/shorts/music_track_registry.json)
- Shorts voice profile registry: [/Users/mike/CascadeEffects/packages/media-pipeline/audio/references/voice_profiles/youtube_shorts_voice_profiles.json](/Users/mike/CascadeEffects/packages/media-pipeline/audio/references/voice_profiles/youtube_shorts_voice_profiles.json)
- Proof review template: [/Users/mike/CascadeEffects/archive/season-01-reference/legacy-fluxlab/proofs/suites/_proof_review_template.md](/Users/mike/CascadeEffects/archive/season-01-reference/legacy-fluxlab/proofs/suites/_proof_review_template.md)

## Policy References

- Stage gates, promotion rules, and resets: [references/stage_gate_policy.md](references/stage_gate_policy.md)
- Motion backend and dual-model matrix policy: [references/motion_backend_policy.md](references/motion_backend_policy.md)
- Source-derived archival reanimation policy: [references/source_derived_archival_reanimation_policy.md](references/source_derived_archival_reanimation_policy.md)
- Caption, text, and final-export handoff policy: [references/caption_and_final_export_policy.md](references/caption_and_final_export_policy.md)

This skill is not for long-form episode video, long-form audio script production, replacing approved long-form assets, or publishing a final without the final-export skill. Long-form is audio-only; motion/video production is the YouTube Short path.

## Outcome Contract

This skill produces or updates:

- a short-specific production pilot and stage ledger
- a narration map for script/audio timing only
- a workflow scope manifest before any visual research
- a DP research brief before visual research
- a DP-owned archival footage review when archival motion is in scope
- a beat-zone visual research packet with ranked artifact and scene options
- a production model decision choosing the cheapest viable lane for an engaging Short
- a research-driven visual beatmap after visual research
- a DP shot plan derived from the visual beatmap, including an editorial spine brief
- a DP-approved active episode constraint ledger before still generation
- a render authorization check before still or motion generation
- a motion readiness review before still/keyframe generation
- source-derived archival reanimation candidates when archival motion is the best visual lane
- a shot-level timing EDL before motion video proof
- a first-second hook local review set when retrofitting an approved/local Short opening
- stage handoff packets for script, audio, contact sheets, proofs, and final export
- dispositioned still and motion review notes
- a keeper lesson capsule after any publishable Short
- a package-level publish manifest and validation result after a keeper video final
- unlisted review upload/status/delete receipts through the publish skill when authorized
- explicit deferred gaps, reset decisions, and `may_advance` calls

This skill does not itself produce the captioned publishable final; it routes `video final` to the final-export skill. It also does not upload or release public videos directly; it routes post-final package validation, unlisted review upload, status checks, and confirmed review-upload deletion to the publish skill.

## Required Inputs

- `episode_id`, `short_id`, source writer packet path, fact-checked long-form audio script path, long-form fact-check report path, short-specific script path, narration map path, cue ranges, and timing intent
- short-specific packaged audio path, transcript path, audio package path, expected voice profile, package hash, transcript hash, and audio disposition once audio is complete
- workflow scope manifest path and DP research brief path before visual research
- archival footage review path when the scope manifest imports motion-reference video
- visual research packet path once research is complete
- production model decision path before the visual beatmap
- visual beatmap path and DP shot packet path before ledger activation
- active episode constraint ledger path before still generation
- render authorization check path before still or motion generation
- motion readiness review path before still/keyframe contact sheet
- short visual workspace or manifest path for generated stills and motion
- active source-preserving documentary judgment docs, used only through the current scope and active ledger
- first-second hook retrofit requests require the latest local publish MP4 path, registered opening impact audio asset, cold-flash prebeat context, frame strip, waveform/loudness evidence, and local review note before any final rebuild may be requested

## Stage Ownership And Gates

1. `script`: coordinator-owned. Require a source writer packet, a fact-checked long-form audio-only script approved by the episode production skill, a derived 60-second Short script, a closing Signature Consequence Motif unless explicitly waived, and a narration map. The narration map records cue ranges, causal lines, and timing intent only; it must not lock the final visual beat structure before research.
2. `audio`: owned by the audio skill. Audio must be `keep`, packaged, hashed, transcript-backed, matched to the active Shorts voice profile, and carry a passing Signature Consequence Motif ending cadence before visual stages advance.
3. `DP scope/research brief`: owned by the DP skill. Before visual research, require a DP-approved workflow scope manifest for the new Challenger short root and a DP research brief built from the short script, audio transcript, and narration map.
4. `visual research packet`: owned by the visual style skill under DP scope. It may read only scoped active roots, exact whitelisted source/audio files, and exact DP-approved imports. It must rank actual research artifacts and scene families for downstream still/motion potential before the beatmap is locked. When archival motion is in scope, complete a DP-owned `archival footage review` first. That review is the clip-level source of truth for archival motion, must use `archival role: hybrid`, `hygiene rule: strict clean`, `analog look: selective`, and `source breadth: 1-3 primary archival videos plus a small backup set`, and must reject any span with logos, stingers, lower-thirds, watermarks, burned captions, end cards, split screens, or channel bugs. The packet is incomplete unless each beat zone records artifact ranking, engagement and mechanism-visibility scores, preferred and backup artifacts, `preferred_clip_ids`, `backup_clip_ids`, `footage_family_id`, `archive_reference_mode`, `texture_influence`, `source_anchor_id`, `recognizable_source_anchor`, `source_anchor_paths_or_urls`, `anchor_preservation_rule`, `carrier_mode`, and `anchor_drift_fail_conditions`, or records a DP-approved `nonliteral_exception_approved`.
5. `production model decision`: coordinator-owned with DP input. After visual research and before the visual beatmap, choose the episode’s primary lane: `source_led_motion`, `source_derived_reanimation`, `sourced_stills`, `generated_stills`, or `hybrid`. This is a lightweight gate that records the cheapest viable path to an engaging Short, the 2-4 hero source families, known source limitations, and whether AI still generation is exception-only or expected. If the decision cannot name strong source families or a justified generation lane, route back to visual research instead of locking the beatmap.
6. `visual beatmap`: DP-owned. After visual research and the production model decision, the DP converts the strongest ranked artifact families into the canonical visual beat structure for the short. Challenger uses a `9 beats + short pre-beat` target. This is the first artifact that may lock the final visual spine.
7. `DP shot planning`: owned by the DP skill. `shot_plan_v2` must derive from the approved visual beatmap, not directly from script paragraphs. Every shot must reference `visual_beat_id` and include the editorial spine brief: hero source families, source-family budget, continuity vector, and any subject/event coverage that should beat literal narration coverage.
8. `episode constraint ledger`: DP-owned. Before render authorization or still generation, require a DP-approved ledger with `ledger_status: active`. The ledger must classify Challenger/Hyatt/Therac/737 and past model constraints as `active`, `conditional`, `legacy_reference`, or `retired`.
9. `render authorization check`: coordinator-owned with DP/style input. Before still or motion generation, record whether an approved source clip/still already solves the shot, whether source-derived reanimation is the better lane, or whether generated stills are actually necessary. The check must set `render_authorization_read: pass|tighten|reject`; a sourced shot with no documented need for generated stills must not enter Flux by default.
10. `motion readiness review`: owned by the motion readiness skill. Before still/keyframe generation, run `shorts_clip_motion_readiness` against the approved shot plan, active ledger, visual research, and render authorization. It must record `motion_readiness_review_path`, `motion_readiness_read`, `motion_affordance`, `locked_surfaces`, `allowed_motion_surfaces`, `banned_motion`, and `failure_route`. A shot with `motion_readiness_read: tighten|reject` cannot enter still/keyframe generation until the still plan, source span, keyframes, or DP coverage is repaired.
11. `stills/keyframe contact sheet`: owned by the visual style skill. This stage is a shot-lock, source-frame, keyframe, and carrier-selection gate, not an automatic Flux-generation stage. Render clean candidates first from approved archival still exports, restored research assets, or clean composites/crops built from restored source assets, then build the contact sheet directly from those full-frame clean candidates. If an approved sourced archival still, frame export, or research crop already solves the shot, review that asset directly instead of generating a replacement AI still. The default review surface must preserve the raw image tiles while carrying the beat info directly on the sheet as minimal plain-text labels only. Do not add borders, blurred fills, padded presentation tiles, or other stylistic review treatments unless the user explicitly requests a separate diagnostic surface. A sidecar index may exist as supplemental metadata, but it must not replace on-sheet beat labels on the default review surface. Each reviewed case must record `generation_source_paths`, `clean_candidate_path`, `contact_sheet_tile_path`, `generation_surface_clean`, `carrier_mode`, `anchor_match`, `coverage_read`, `variety_read`, `engagement_read`, `hygiene_read`, and `motion_readiness_review_path`. Any still that collapses into anonymous evidence-room drift, low-energy repetitive evidence coverage, absorbed archival contamination, review-surface contamination, or a motion-readiness failure must route back upstream instead of advancing.
12. `stills video proof`: coordinator-owned when still/keyframe pacing needs review. Assemble selected stills against approved audio to test pacing, coverage, beat order, and timing. Proof segments must render from `clean_candidate_path`, not from any styled review surface. A sourced still is a valid proof input; no generated still is required when the approved sourced asset already solves the shot.
13. `motion contact sheet`: owned by the visual style skill and promotion workflow. This stage consumes approved source surfaces from the still/keyframe lane and the archival review; it must not harvest replacement imagery on the fly. The candidate grid may compare `direct_source_clip`, `source_derived_reanimation`, and `still_driven_i2v` handles when those strategies were approved upstream. Source-derived archival reanimation means a generated beat-length motion handle from clean source frames/keyframes in a reviewed archival span. Motion contact sheets must reference the early `motion_readiness_review_path` so failures are routed back to still/source planning instead of repeated motion rerenders. Review every completed MP4 end-to-end and audit dense representative frames before handoff; manifest-only review or sparse thumbnail inspection is insufficient. For launchpad, plume, vehicle, rigid-geometry, historical machinery, explosion, human/tableau, clinical, or other high-risk beats, require frame-by-frame or near-frame-by-frame review before the candidate can be surfaced. Motion proof clips must target at least `5.0` seconds even when the underlying beat is shorter; treat that as the floor for diagnostic motion evaluation. All motion candidates are visual-only; backend-generated or source-retained audio must be stripped before contact sheets or proof assembly. If archival source quality is weak because full-bleed vertical framing crops a low-resolution source too aggressively, run an `archival_cleanup_scout` first. That scout must compare current normalized baseline MP4s against conservative FFmpeg cleanup, record `source_resolution`, `crop_width_px`, `upscale_factor`, `enhancement_lane`, `restoration_recipe_id`, `enhancement_read`, `artifact_read`, and `source_limit_read`, and block motion proof promotion until human review passes. Do not use AI upscaling, synthetic detail, face restoration, pillarbox/matte framing, or global HD modernization unless a later explicit scope approves it.
   Before any motion video proof, build an explicit `shot_timing_edl`, with one row per actual story shot. Normal story shots must be at least `2.0` seconds unless a later approved episode rule raises the floor, and every source-native camera/edit cut must either become its own EDL row or be avoided with a cleaner source span or stable source-frame hold. Do not claim a five-second beat handle satisfies the rule when the underlying source flashes through sub-second shots. The shot-level contact sheet is the timing authority; any beat rollup sheet is secondary continuity evidence only. The EDL supersedes the five-second diagnostic handle floor for proof-minded edit review: actual proof story shots follow the approved audio timing but still obey the `2.0` second minimum unless explicitly waived.
   If the user rejects a timing repair because it is not materially different, do not keep iterating inside the same sequence shape. Mark the pass `reject`, keep proof blocked, and route to an editorial rebuild that reselects source families, shot order, and beat coverage while preserving approved audio and hard endpoints.
   For Shorts, judge visual coverage as if a human is scrolling a feed. When a strong event/subject family exists, it should beat low-energy institutional rooms, hearings, admin tables, paperwork, or process coverage unless the room shot is itself the most visually compelling carrier. The voiceover can carry causal detail; the image should carry attention. For Challenger-like event shorts, shuttle/pad/launch/ascent/failure imagery must dominate over hearing/control-room coverage, and room/human material should be only brief context unless a DP override records why it will outperform the subject.
14. `house CRT/signal-interruption policy planning`: coordinator/DP-owned. Before proof/final, rows may record `texture_influence: house_crt` and the required final look, but the publishable house CRT/signal-interruption treatment is not baked into captions or treated as era-specific archival texture. This is a cross-episode brand texture: do not choose film, institutional-video, 1990s-news, 2000s-web, or mobile-video profiles by episode period. Use the global `house_crt_luma_neutral_chroma_signal_interruption_v1` contract with the selected visible-line policy: `era_1980s_broadcast_crt_v1`, `visible_but_premium`, `texture_tone_policy: luma_neutral_chroma_visible_scanline_v1`, `calibration_recipe_id: premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1`, and `scanline_strength_variant_id: max_visible_bars_y24_p8`. Challenger-style randomized signal interruption belongs only at eligible story-clip cuts and must not hide failed motion, weak source selection, failed hygiene, or failed frame QA.
15. `motion video proof`: coordinator-owned. Assemble selected `keep` motion winners against approved audio from the approved `shot_timing_edl`, generate a beat sheet beside the proof, and label unresolved cuts as `mixed review short`. Proof story shots follow the approved audio timing, each declared story shot must be at least `2.0` seconds unless explicitly waived, and no hidden source-native cut may create sub-second story flashes. The proof review must record `proof_assembled_from_shot_timing_edl`, `contact_sheet_to_proof_parity_read`, `hidden_cut_read`, `story_shot_duration_read`, and `motion_readiness_review_path`. Proofs remain no-caption picture/timing approvals; final-export owns the mandatory house CRT/signal-interruption rebuild before caption burn.
16. `first-second hook local review`: coordinator-owned for retrofit work only. Inventory the latest local publish MP4, prepend a `0.75s` cold-flash prebeat in a local proof excerpt, start the registered hard impact hit at `t=0.00`, and create side-by-side comparison proof, frame strip at `0.00`, `0.12`, `0.25`, `0.50`, `0.75`, and `1.00`, waveform/loudness evidence, manifest, and review note. Record `first_second_hook_context`, `cold_flash_prebeat_context`, `opening_impact_audio_context`, and `first_second_hook_read: pass|tighten|reject`. This gate is local review only: do not shift captions, rebuild publishable finals, trim voice, upload, delete, replace, schedule, or publish until a human records `keep`.
17. `video final`: owned by the final-export skill. Consume the approved motion proof, audio, locked caption text source, ASR/WhisperX timing source, proof review note, caption preset, the final-gate house CRT/signal-interruption manifest, and any human-kept first-second hook context to produce the captioned final and QA packet. The first video-final substep rebuilds the no-caption motion bed through `house_crt_luma_neutral_chroma_signal_interruption_v1`, including Challenger-style randomized `0.25s` signal interruption mutating eligible outgoing segment tails. Captions are the last visual layer: no CRT, signal, static, texture, tail visual, comparison effect, or hook visual effect may run after caption burn; only stream-only audio muxing may happen later. Active Shorts default to the music registry's `paper_architecture_theme_v1` as a manifest-backed `motif_outro_mix` unless the coordinator records `music_policy: waived` or `music_policy: alternate_approved`. Apply music only after approved voice/caption timing is locked; do not route it back through ElevenLabs audio generation.
18. `publish package`: coordinator-owned after a keeper `video final`. Require a local package manifest, upload MP4, title, description, tags, SRT, cover frame, final review, final-export manifest, source-final keeper fields, and SHA-256 values. Validate with `publish-package-check`; rights, Paper Architecture music, source-footage, and Content ID notes are warnings that remain blockers for public release, not blockers for unlisted review upload.
19. `unlisted review upload`: owned by the publish skill. Upload only with `publish-package-upload <manifest_path> --privacy unlisted` after action-time user confirmation. Record the receipt path, video ID, URL, authenticated channel, processing status, thumbnail status, validation warnings, and Studio blockers. Use `publish-package-status` for processing checks. Delete mistaken review uploads only with exact video-id confirmation via `publish-package-delete`; if OAuth lacks delete scope, route deletion to manual Studio cleanup. Public release remains manual.
20. `keeper lesson capsule`: coordinator-owned after a Short reaches publishable `keep`. Record only reusable lessons: production lane choice, winning source families, useful failure modes, final texture/audio/caption/publish decisions, and whether each lesson is global policy, episode-local, or diagnostic history. Do not promote episode-specific imagery or constraints into global rules without an explicit global-policy decision.

For detailed eligibility, hard-beat handling, reset scope, and pass limits, use [references/stage_gate_policy.md](references/stage_gate_policy.md).

## Agent Roles

- `Coordinator / Gatekeeper`: owns stage ledger, routing, artifact paths, blockers, deferred gaps, reset decisions, and `may_advance`.
- `Script Agent`: validates or drafts short-specific script, narration map, cue ranges, and timing intent.
- `Audio Agent`: runs the Shorts ElevenLabs audio workflow and hands off WAV, package, transcript, and provenance.
- `DP Agent`: owns workflow scope, DP research brief, exact legacy imports, visual beatmap approval, active constraint ledger approval, shot design, and motion-coverage planning.
- `Visual Research Agent`: creates the beat-zone visual research packet inside the workflow scope, ranks artifacts for downstream scene strength, and records evidence-backed constraint proposals before still generation.
- `Production Model Decision Agent`: records the source/generation lane and hero source-family budget before visual beatmap lock.
- `Stills/Keyframe Contact Sheet Agent`: reviews clean source frames, keyframes, sourced stills, or generated still candidates and prepares the contact sheet.
- `Stills Video Proof Agent`: builds static timing proof from selected stills and approved audio.
- `Motion Contact Sheet Agent`: renders and reviews motion candidates and prepares the motion contact sheet.
- `Shot Timing EDL Agent`: turns selected motion/source handles into actual story-shot timing before proof assembly.
- `Motion Video Proof Agent`: assembles selected `keep` motion winners from the shot timing EDL and records proof manifest plus beat sheet.
- `First-Second Hook Review Agent`: builds local-only cold-flash prebeat comparison proofs from latest local publish MP4s and records hook evidence without final rebuilds or YouTube action.
- `Final Export Agent`: applies final captions, exports the publishable vertical video, and records final QA through the final-export skill.
- `Publish Agent`: validates package manifests, uploads unlisted YouTube review drafts, checks processing/status, writes receipts, and routes public-release checks to the human Studio flow.

## Handoff Packet

Every stage returns a stage-aware production packet to the coordinator:

```yaml
stage:
episode_id:
short_id:
inputs_used:
artifacts_created:
visual_context: [visual_research_packet_path, reference_sources]
scope_context: [workflow_scope_manifest_path, active_episode_short_root, active_viz_short_root, exact_dp_imports]
dp_context: [dp_research_brief_path, dp_shot_packet_path, shot_plan_v2_path]
script_context: [short_script_path, narration_map_path]
beatmap_context: [visual_beatmap_path, visual_beat_ids, preferred_artifact_ids]
production_model_context: [production_model_decision_path, production_model_lane, hero_source_family_ids, source_family_budget, render_authorization_read]
constraint_context: [episode_constraint_ledger_path, active_constraint_ids, conditional_constraint_ids, legacy_reference_ids, retired_constraint_ids]
source_anchor_context: [source_anchor_ids, carrier_modes, nonliteral_exception_approved, anchor_match]
archival_context: [archival_footage_review_path, footage_family_ids, preferred_clip_ids, archive_reference_modes, texture_influence]
historical_signal_texture_context: [historical_signal_profile_ids, texture_application_scope, house_crt_texture_read, signal_interruption_read, texture_visibility_reads, youtube_survival_reads, compression_artifact_reads, detail_survival_reads]
motion_context: [motion_readiness_review_path, motion_readiness_read, motion_candidate_matrix, selected_motion_clips, motion_source_preferences, source_derived_reanimation_candidates, shot_timing_edl_path, contact_sheet_to_proof_parity_read]
review_paths: [contact_sheet_path, proof_video_path, beat_sheet_path, review_note_path]
coverage_reviews: [coverage_read, variety_read, engagement_read, hygiene_read, generation_surface_read]
audio_context: [short_audio_package_path, expected_voice_profile_id, audio_package_sha256, packaged_audio_sha256, audio_disposition, brand_motif_status, motif_family, motif_text, motif_waiver_reason, ending_cadence_read, ending_cadence_reference_package]
final_music_context: [music_track_registry_path, music_track_id, music_policy, music_waiver_reason, music_rights_check_status, motif_outro_mix_used, body_loop_path, body_loop_sha256, body_loop_volume_linear, body_loop_start_seconds, body_loop_end_seconds, outro_path, outro_sha256, outro_start_seconds, outro_initial_volume_linear, outro_ramp_start_seconds, outro_ramp_end_seconds, outro_ramp_end_volume_linear, visual_extension_mode, final_frame_hold_seconds, source_motion_tail_path, source_motion_tail_source_clip_id, source_motion_tail_source_span_in, source_motion_tail_source_span_out, source_motion_tail_residual_hold_seconds, motif_music_bed_read, outro_completion_read, final_mix_peak_db]
first_second_hook_context: [first_second_hook_manifest_path, local_review_set_path, current_latest_publish_mp4_path, revised_first_second_proof_path, comparison_proof_path, frame_strip_path, waveform_path, cold_flash_prebeat_context, opening_impact_audio_context, first_second_hook_read, human_review_disposition]
caption_context: [caption_model, caption_text_source_path, caption_timing_source_path, caption_text_source_policy, caption_timing_source_policy, caption_text_matches_script_read, caption_asr_text_not_used_read, caption_style_preset, caption_placement]
publish_context: [publish_package_manifest_path, publish_package_check_status, review_upload_receipt_path, youtube_video_id, youtube_video_url, privacy_status, processing_status, thumbnail_status, delete_receipt_path, public_release_boundary]
keeper_lesson_context: [keeper_lesson_capsule_path, reusable_lesson_count, global_policy_candidates, episode_local_lessons]
disposition: keep | tighten | diagnostic only | reject
reel_class: keeper short | mixed review short
blockers:
deferred_gaps:
next_action:
may_advance: true | false
```

Only the coordinator may set `may_advance: true`.

## Hard Rules

- Use only `keep`, `tighten`, `diagnostic only`, and `reject`.
- Reel/final classes are `keeper short` and `mixed review short`.
- Paper Architecture visual style is not allowed for YouTube Shorts video assets. Do not use `cascade-paper-architectures-ink-lit-v1`, folded-paper/foam-core source art, paper-model tableaux, or Paper Architecture resemblance for Shorts stills, keyframes, motion candidates, proof frames, final frames, cover frames, in-video graphics, or thumbnails. If any active Shorts artifact contains that visual style, set `paper_architecture_visual_style_read: reject`, keep `may_advance: false`, and route back to source-preserving documentary planning. This does not prohibit the registered `paper_architecture_theme_v1` music track or Paper Architecture music claim notes.
- First-second hook retrofits must start with picture and impact audio at `t=0.00`; black frame or silence at `t=0.00` is `reject`.
- A cold-flash prebeat defaults to `0.75s`; it must be scene-led or event-led, must show a recognizable episode subject or event by `<=1.00s`, and must not use default admin, paperwork, or process coverage unless a recorded exception explains why it outperforms the subject/event.
- First-second hook local review sets must not shift final captions, rebuild publishable finals, upload, delete, replace, schedule, or publish. After human `keep`, final rebuilds may offset narration/captions; if duration exceeds target, trim nonessential visual hold or tail time first and never trim the spoken motif, voice cadence, or required caption content.
- Only `keep` audio advances into visual work; only `keep` source surfaces, keyframes, source clips, or stills are eligible for motion; only `keep` motion clips are eligible for final.
- Active Shorts must use `youtube_shorts_mike_challenger_match_v1` unless the coordinator explicitly promotes a new active profile in the audio lane registry.
- Every active Cascade Effects YouTube Short must end with the Signature Consequence Motif unless the coordinator records an explicit waiver. The default motif is `Small causes, massive consequences.`
- Lane-level motif variants are valid when the coordinator records `brand_motif_status: variant`, `motif_family`, exact `motif_text`, and passing cadence QA. The approved `Mystery That Has Receipts` motif family is `mystery_that_has_receipts` with `motif_text: The mystery fades. The receipts remain.`
- The motif is a spoken ending, not only caption text. The audio package, motion proof manifest, and final export manifest must carry `brand_motif_status`, `motif_text`, and `ending_cadence_read`.
- A correct motif transcript is not sufficient if delivery sounds unresolved. `ending_cadence_read` must be `pass`; question-like terminal lift, cut-off delivery, or missing post-line resolution reopens audio and downstream timing/final export.
- Active Shorts default to `music_policy: canonical_default` with `music_track_id: paper_architecture_theme_v1` from the music track registry unless the coordinator records a non-empty `music_waiver_reason` or a registry-backed approved alternate track.
- When a final music bed or theme outro is used, the Signature Consequence Motif remains the semantic ending. The body loop must support the voiceover without competing with it; the outro may begin quietly before the final motif resolves, but its audible ramp should occur after the motif lands. Start with a short final-frame hold of about `0.5-0.75` seconds, and extend visual duration only when the registered track's `outro_completion_policy` requires it so the outro is not cut off. If that extension creates a visible freeze and approved clean continuation footage exists, use a no-audio `source_motion_tail` instead of cloned-frame padding. Record `music_track_registry_path`, `music_track_id`, `music_policy`, `music_rights_check_status`, loop/outro source hashes, visual extension mode, `motif_music_bed_read: pass|tighten|reject`, `outro_completion_read: pass|tighten|reject`, final-frame hold duration, source tail path/span when used, outro duration used, cutoff seconds, and final mix peak level in the final export manifest.
- Active short manifests, proof manifests, and final export manifests must carry the required audio package, script-locked caption text source, timing source, disposition, voice-profile, and hash fields.
- Shorts caption model is `script_locked_canonical_text_timing_from_asr_v1`: locked short script text is the caption word source; WhisperX/ASR/SRT/VTT evidence is timing only.
- `.diarized.*`, WhisperX, raw ASR, VTT, and SRT timing files are blocked as caption word sources unless they are already script-locked outputs with passing QA.
- Final and publish package manifests must record `caption_text_source_path`, `caption_timing_source_path`, `caption_text_matches_script_read: pass`, `caption_asr_text_not_used_read: pass`, and that burned-in and player sidecar captions derive from the same script-locked source.
- Post-final publishing is package-based only. Use `publish-package-check`, `publish-package-upload --privacy unlisted`, `publish-package-status`, and exactly confirmed `publish-package-delete`; never use deprecated episode-level publish commands for Shorts.
- YouTube public release remains manual. Agents may not make a Short public or schedule publication programmatically.
- Manual Studio checks before public release must include copyright/Content ID, Paper Architecture music claim state, altered-content disclosure, captions, cover frame, audience, metadata, and visibility.
- Burned-in captions cannot be disabled on YouTube; uploaded SRT or auto captions should be reviewed or removed if they duplicate the burned-in caption layer.
- New Challenger visual production must begin from a new scoped short root, not old `challenger_short_v1`, `v2`, `v3_trimmed`, or `restart` visual folders.
- Visual context may hydrate only from the workflow scope manifest, exact whitelisted source/audio files, and exact DP-approved imports.
- `/archive/`, `/archives/`, `/experiments/`, `/legacy/`, `/retired/`, `/midjourney/`, `/proof_stills/`, diagnostic outputs, mixed-review outputs, old renders, old manifests, old casebook/keeper-derived constraints, and old model experiment rules are blocked by default.
- A DP-approved workflow scope manifest, DP research brief, visual research evidence packet, research-driven visual beatmap, DP shot packet, and active episode constraint ledger must exist before still generation.
- No old Challenger, Hyatt, Therac, or 737 constraints become active automatically.
- The narration map must precede visual research. The visual research packet must precede the production model decision. The production model decision must precede the visual beatmap. The visual beatmap must precede `shot_plan_v2`. `shot_plan_v2` must precede the active episode constraint ledger. The active ledger must precede the render authorization check. The render authorization check must precede motion readiness review. Motion readiness review must precede still/keyframe generation; each later stage must follow the canonical flow in order.
- The narration map is not a visual lock. Do not treat script paragraphs or cue ranges as permission to skip the research-driven visual beatmap step.
- When archival motion is in scope, the archival footage review must precede the visual beatmap and must be referenced by the visual research packet, visual beatmap, and DP shot plan.
- Every beat or shot must have a recognizable source anchor or an explicit DP-approved non-literal exception before still generation may begin.
- `carrier_mode` must be recorded as `generated`, `sourced`, or `hybrid`. Approved historical crops or sourced stills are allowed live carriers when that path is explicitly reviewed and recorded; this is not the same as copying a reference image into a prompt.
- If an approved sourced visual-research still, archival still export, or clean archival clip already solves the shot, do not create a replacement AI still just to animate it later. Use the sourced asset directly for proof or motion preparation and treat generated stills as exception-only.
- If archival footage gives the correct visual language but the edit needs timing control, use `source_derived_reanimation`: clean source span plus same-shot keyframes plus an audited no-audio LTX handle. Do not collapse this back into Flux still generation.
- Motion strategy values are `direct_source_clip`, `source_derived_reanimation`, `direct_source_still`, `still_driven_i2v`, `generated_still`, and `hybrid_generated`.
- `source_derived_reanimation` candidates must record source clip id/path/span, start/end keyframes, same-camera confirmation, crop consistency, raw output, normalized no-audio output, frame-audit paths, temporal/physical/source-alignment reads, archival fidelity read, and disposition.
- Motion candidates are visual-only. Any backend-generated or source-retained audio must be stripped, and the only approved audio in proofs or finals is the coordinator-approved short audio.
- A motion video proof cannot start from beat handles alone. It must have an approved `shot_timing_edl`; missing EDL, unlisted source-native cuts, sub-`2.0` second story flashes, or contact-sheet/proof drift are `tighten` or `reject`.
- `generation_source_paths`, `clean_candidate_path`, and the raw `contact_sheet_tile_path` derived from `clean_candidate_path` are the only authoritative still-generation and review-display surfaces by default. Any optional `review_plate_path`, any compiled `contact_sheet*.png`, and any file under `stills/contact_sheet_pass_*/raw/` are non-authoritative review artifacts.
- If a case uses `source_kind: research_board_composite`, the board composite is selection-only and may not enter proof or generation until the case resolves to real clean source files recorded in `generation_source_paths`.
- Archival motion imports require exact local media paths plus original source URLs or origin notes in the workflow scope manifest and archival footage review.
- Keep archival source breadth narrow: up to `3` primary videos plus up to `2` backups for a short.
- One strong archival footage family may satisfy multiple narration lines. Do not force one literal visual per script clause.
- Under `strict clean`, any visible logo, stinger, lower-third, watermark, burned caption, end card, split screen, or channel bug is an automatic archival clip reject. Do not rely on crop or cleanup fallback in this pass.
- For Challenger, technical/evidentiary insert coverage is support-only: one insert-heavy beat family or two insert shots total unless the DP records an override.
- `texture_influence` values are `none|house_crt`. For active Shorts, plan `house_crt` on story clips that enter proof/final unless the coordinator records an explicit waiver. The former `selective_archival`/era-matched policy is legacy; do not select texture by historical period or source medium. Final export must record `house_crt_static_context` with `house_crt_contract_id: house_crt_luma_neutral_chroma_signal_interruption_v1`, `source_lineage_read.clean_source_confirmed: true`, `house_crt_texture_read.profile_id: era_1980s_broadcast_crt_v1`, `house_crt_texture_read.intensity: visible_but_premium`, `texture_tone_policy: luma_neutral_chroma_visible_scanline_v1`, `calibration_recipe_id: premium_broadcast_crt_luma_neutral_chroma_visible_scanline_v1`, `scanline_policy_id: luma_neutral_visible_scanline_modulation_v1`, `scanline_strength_variant_id: max_visible_bars_y24_p8`, `scanline_delta_y: 24.0`, `scanline_period_pixels: 8`, `scanline_band_pixels: 2`, `luma_chroma_metrics_read.overall_read: pass`, `signal_interruption_read.profile_id: era_1980s_horizontal_signal_interruption_v2_randomized`, `duration_seconds: 0.25`, `timing_policy: replace_outgoing_segment_tail_preserve_total_duration`, `full_frame_static_replacement_used: false`, and `visual_layer_order_read.caption_burn_is_last_visual_operation: true`, or an explicit waiver. The interruption is a Challenger-style mutation of outgoing footage; do not use full-frame static as a story-footage mask.
- The DP must apply the `engaging and visually stimulating` thesis during visual research artifact selection. Scene-led research artifacts come first, mechanism inserts come second, and low-energy paperwork or evidence-room props are exception-only.
- Apply a Shorts scroll test before promoting visual or motion coverage: if a gorgeous subject/event image is available and a hearing room, control room, admin table, or process shot is not visually competitive, use the subject/event image and let narration carry the institutional logic. Record any exception as `scroll_stop_exception_approved`.
- Still prompts must use the approved visual research packet plus only the active ledger constraints. The visual judgment docs may be consulted as scoped references but cannot activate constraints by themselves.
- If a reviewed still loses recognizable relation to its source anchor and reads like a generic evidence-room object, disposition it `tighten` or `reject`, record `anchor_match: reject`, and route back to visual research or DP carrier planning. Name that failure mode `anonymous evidence-room drift`.
- If a sourced or hybrid output inherits logos, stingers, lower-thirds, burned captions, or channel bugs from archival footage, disposition it `tighten` or `reject`, record `hygiene_read: reject`, and name the failure mode `absorbed archival contamination`.
- If a styled contact plate, blurred-fill composite, framed review artifact, or compiled contact sheet enters generation or proof as if it were a clean source still, disposition it `tighten` or `reject`, record `generation_surface_read: reject`, and name the failure mode `review-surface contamination`.
- Generated stills and motion text/logo/caption controls are not inherited from legacy docs; they must be active in the current ledger if they are to control generation. Final YouTube Shorts captions still belong only in `video final`.
- No diagnostic placeholders in a `keeper short` or `video final`.
- No silent mutation of approved long-form episode manifests, long-form audio masters, or long-form rough cuts.
- Long-form audio packages are cataloged only and must not enter Shorts manifests, proofs, or finals.

## Required Artifacts

Output should be a stage-aware production packet, not a generic status note. Name the current stage, gate result, artifact paths, blockers, deferred gaps, and the next required specialist skill.

- short production pilot using [templates/short_production_pilot_template.md](templates/short_production_pilot_template.md)
- narration map using [templates/narration_map_template.md](templates/narration_map_template.md)
- visual beatmap using [templates/short_beat_shot_plan_template.md](templates/short_beat_shot_plan_template.md)
- workflow scope manifest using [/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/workflow_scope_manifest_template.md](/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/workflow_scope_manifest_template.md)
- DP research brief using [/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/dp_research_brief_template.md](/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/dp_research_brief_template.md)
- DP shot packet using [/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/dp_shot_packet_template.md](/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/dp_shot_packet_template.md)
- episode constraint ledger using [/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/episode_constraint_ledger_template.md](/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/episode_constraint_ledger_template.md)
- visual research packet using [templates/visual_research_packet_template.md](templates/visual_research_packet_template.md)
- production model decision using [templates/production_model_decision_template.md](templates/production_model_decision_template.md)
- render authorization check using [templates/render_authorization_check_template.md](templates/render_authorization_check_template.md)
- motion readiness review using [/Users/mike/CascadeEffects/ops/agents/skills/motion_readiness_v1/templates/motion_readiness_review_template.md](/Users/mike/CascadeEffects/ops/agents/skills/motion_readiness_v1/templates/motion_readiness_review_template.md)
- shot timing EDL using [templates/shot_timing_edl_template.md](templates/shot_timing_edl_template.md)
- archival footage review using [/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/archival_footage_review_template.md](/Users/mike/CascadeEffects/ops/agents/skills/director_of_photography_v1/templates/archival_footage_review_template.md) when archival motion is in scope
- keeper lesson capsule using [templates/keeper_lesson_capsule_template.md](templates/keeper_lesson_capsule_template.md) after a publishable keeper short
- optional packet skeleton generator: [scripts/visual_research_packet_skeleton.py](scripts/visual_research_packet_skeleton.py)
- deferred-gap list using [templates/deferred_gap_template.md](templates/deferred_gap_template.md)
- proof and final review note using [templates/short_video_stage_review_template.md](templates/short_video_stage_review_template.md)
- first-second hook local review note using [templates/first_second_hook_review_template.md](templates/first_second_hook_review_template.md)
- motion contact sheet manifest using [templates/motion_contact_sheet_manifest_template.md](templates/motion_contact_sheet_manifest_template.md)
- final-export request using [/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_final_export_v1/templates/final_export_request_template.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_final_export_v1/templates/final_export_request_template.md)
- proof reviews using [/Users/mike/CascadeEffects/archive/season-01-reference/legacy-fluxlab/proofs/suites/_proof_review_template.md](/Users/mike/CascadeEffects/archive/season-01-reference/legacy-fluxlab/proofs/suites/_proof_review_template.md)

## Worked Example

Use Challenger restart as the primary worked example for this skill. Old v1/v2/v3/restart visual folders are legacy reference unless exact files are DP-imported.

- new scoped short root: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/<new_challenger_short_id>/`
- new scoped visual root: `/Users/mike/CascadeEffects/packages/media-pipeline/viz/references/episodes/challenger/shorts/<new_challenger_short_id>/`
- source writer packet: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/writer_packet.md`
- source long-form script: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/Ep1_Challenger.txt`
- long-form fact-check report: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/fact_check.md`
- accepted prior audio source, usable only as exact whitelisted audio provenance: `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/challenger_short_restart_v1/final/challenger_short_restart_v1.wav`

## Edge Cases

- If short audio is not promotable, unregistered, wrong-profile, wrong-model, missing hashes, or long-form-sourced, route back to `audio`.
- If workflow scope manifest, DP research brief, visual research evidence, or active episode constraint ledger is missing, block still generation and route to the DP-owned missing artifact.
- If the narration map is missing, block visual research and route back to `script`.
- If the visual beatmap is missing after research, block `shot_plan_v2`, ledger activation, and stills.
- If an agent tries to hydrate from archives, experiments, old renders, old manifests, or old episode constraints without an exact DP import, stop and route back to scope/import approval.
- If the visual research packet is missing, stale, or too vague to constrain canonical subjects, scene families, artifact rankings, and anomaly carriers, route back to `visual research packet`.
- If archival motion is in scope and the archival footage review is missing, stale, lacks exact local paths, exceeds the narrow source cap, or has unresolved hygiene failures, block the beatmap and route back to the DP archival review.
- If the visual research packet cannot name a recognizable source anchor for a beat or shot and DP has not approved a non-literal exception, block still generation.
- If a sourced or hybrid archival span carries logos, bugs, stingers, lower-thirds, end cards, or burned captions, reject it instead of planning cleanup.
- If visual research cannot provide at least two strong scene-led or mechanism-led artifact options for a Challenger beat zone when the source package offers them, rerun research for that zone instead of collapsing into flat admin props.
- If the production model decision is missing, stale, or chooses generated stills without a source-first rationale, block the visual beatmap.
- If render authorization is missing or says a sourced asset already solves the shot, block still or motion generation until the lane is corrected.
- If `shot_timing_edl_path` is missing before motion proof, block proof assembly.
- If a publishable Short has no keeper lesson capsule, do not block publishing, but require the coordinator to create the capsule before starting the next episode lane.
- If a contact sheet drifts into anonymous evidence-room carriers, change the carrier or use a sourced still instead of endlessly tightening wording.
- If a short is alternate, experimental, or comparison-only, keep it isolated and unpromoted.
- If long-form assets are the only starting point, create an isolated short lane first before production work.
- If a proof lacks a beat sheet, generate one beside the proof and record `beat_sheet_path` before review.
- If a specialist tries to skip directly to `video final`, route back to the coordinator and enforce the missing gates.
- If a first-second hook retrofit lacks latest local publish inventory, registered impact audio, frame strip, waveform evidence, or a human `keep`, keep the phase local and do not request a final rebuild.
