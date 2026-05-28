---
name: "long_form_video_production_v1"
description: "Coordinate Cascade Effects long-form YouTube video production as watchable audio essays with living-cover visuals, required music-integration contracts, brand-system guidance, existing asset inventory, and human review gates before each phase."
---

# Long-Form Video Production v1

Use this skill for Cascade Effects long-form YouTube video production, watchable audio essays, living-cover visuals, long-form video packaging, full-episode upload preparation, and long-form video review packets.

This skill owns the gated long-form video workflow:

`inventory -> episode package -> visual system plan -> living-cover cue map -> ambient/effects layer -> music integration contract -> motion readiness review -> rough assembly proof -> final assembly -> publish readiness -> post-publish learning`

For rough/final advancement, the required gate chain is `music integration contract -> rough assembly proof -> final assembly`; motion-readiness review may occur between the contract and rough proof, but it does not waive the music contract.

The long-form video is the canonical episode. Existing Shorts are bridge assets and discovery surfaces, not the production source of truth.

## Required References

- Series strategy and mechanism alignment: [/Users/mike/CascadeEffects/ops/agents/skills/cascade_effects_series_bible_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/cascade_effects_series_bible_v1/SKILL.md)
- Brand visual source of truth: [/Users/mike/CascadeEffects/apps/web/brand](/Users/mike/CascadeEffects/apps/web/brand)
- Design-system contract: [/Users/mike/CascadeEffects/apps/web/brand/contracts/design-system.contract.md](/Users/mike/CascadeEffects/apps/web/brand/contracts/design-system.contract.md)
- Illustration contract: [/Users/mike/CascadeEffects/apps/web/brand/contracts/illustration.contract.md](/Users/mike/CascadeEffects/apps/web/brand/contracts/illustration.contract.md)
- YouTube channel asset package: [/Users/mike/CascadeEffects/apps/web/brand/packages/youtube-channel.package.json](/Users/mike/CascadeEffects/apps/web/brand/packages/youtube-channel.package.json)
- Living Cover system spec: [/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md](/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md)
- Episode visual-system baselines: [/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/episode_visual_system_baselines/index.json](/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/episode_visual_system_baselines/index.json)
- Production output contract registry: [/Users/mike/CascadeEffects/packages/contracts/cascade_effects_output_contracts.v1.json](/Users/mike/CascadeEffects/packages/contracts/cascade_effects_output_contracts.v1.json)
- Publish-readiness backfill prompt: [/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/publish_readiness_backfill_prompt.md](/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/publish_readiness_backfill_prompt.md)
- VO/outro blend backfill prompt: [/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/vo_outro_blend_backfill_prompt.md](/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/vo_outro_blend_backfill_prompt.md)
- YouTube metadata copywriting: [/Users/mike/CascadeEffects/ops/agents/skills/youtube_metadata_copywriting_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_metadata_copywriting_v1/SKILL.md)
- Shorts production, only for new or revised Shorts: [/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md)

## Scope

This skill may produce or update:

- episode asset inventory
- frontier-model script critique packet and integration note before long-form audio render
- human script approval record for audio render authorization
- long-form video production plan
- visual system plan guided by the brand contracts
- Living Cover visual-system plan and HTML rough-proof packets using `living_cover_system_v1`
- Living Cover generation provenance records for generated raster, video, and deterministic composition carriers
- Living Cover ambient/effects layer plans and QA reads
- Living Cover music integration contracts, timing offsets, mix/rights reads, and waiver records
- chapter map, Living Cover cue map, and typography cue map
- Short candidate map and publishing wave note when a Shorts expansion is scoped
- rough assembly proof review packet
- final assembly review packet
- YouTube packaging checklist
- HTML publish-readiness review package
- post-publish learning note

This skill must not:

- produce new Shorts or bypass the Shorts production skill
- make public uploads or change YouTube visibility
- treat legacy visual artifacts as active without explicit human review
- replace approved long-form audio masters unless the user explicitly requests audio revision
- render, promote, or keep long-form voice audio from a script that lacks both frontier-model script critique and explicit human script approval for audio
- invent a per-episode visual system before checking the brand contracts
- start episode source-art, backplate, or Living Cover visual-system work from scratch when an episode baseline exists; load the baseline first and record any deviation
- advance a phase without a recorded human review disposition

## Core Rules

- Long-form videos are watchable audio essays: audio-first, video-aware, easy to produce, and still worth looking at.
- Local HTML media reviews must be served through the repo range server, never `python -m http.server`, plain `file://`, or another server that has not passed a `Range: bytes=0-1023` probe. Before giving a local review URL for any long-form proof, final, publish-readiness package, or other page with audio/video scrubbing, start or verify `node scripts/range_static_server.mjs 8766 /Users/mike/CascadeEffects/archive/season-01-reference/original-episodes`, then run `node scripts/probe_review_range_server.mjs REVIEW_URL`. The probe must return `206 Partial Content` plus `Accept-Ranges: bytes` and `Content-Range`; record/pass `html_range_server_read` or the packet-specific equivalent. If the probe fails, stop and fix the server before asking for human review.
- Long-form audio render authorization is a hard pre-audio gate. Before sending any long-form script to ElevenLabs, OpenAI, or another TTS provider, the exact script revision must have: `frontier_model_script_critique_read: pass`, `critique_integration_read: pass`, and `human_script_approval_for_audio_read: pass`.
- Claude is the default frontier-model script critic unless unavailable or explicitly replaced by a human-approved equivalent frontier model. Record the critic model/tool, critique prompt or transcript path/hash, script path/hash reviewed, critique summary, required changes, integration/defer rationale, post-integration script path/hash, and final human approval artifact.
- A TOML `script.status = "locked"` value is not enough to authorize long-form audio rendering. It only identifies the candidate source text; it does not satisfy frontier critique, integration, or human approval.
- Existing audio rendered without the frontier-model critique and human script approval records is `diagnostic_only` or `review_ready_blocked_missing_script_gate`. It cannot be marked `keep`, cannot satisfy the Episode Package Gate, and cannot open Visual System, Rough Assembly, Final Assembly, Publish Readiness, upload, or release until the missing script gate is backfilled or an explicit human waiver names the episode and affected output.
- The video should feel like a living cover: ambient motion, structured chapters, occasional visual punctuation, and strong sonic identity.
- Receipts/legend long-form episodes should use `long_form_receipts_legend_signoff_v1` when the public story, myth, or legend is narrowed by source evidence: `The legend fades. The receipts remain.` This sign-off follows the episode-specific synthesis and any series motif such as `The failure was real. The cause chain was longer.` If this terminal VO changes after audio is rendered, the existing WAV, transcripts, timing sidecars, audio source integrity report, and audio review note become stale until a fresh approved-script render proves the new line.
- Living Cover cues must be planned as an explicit artifact before rough assembly. The cue map records chapter shifts, key phrase typography, effect-map moments, source-safe motion/composition treatments, caption/rail coordination, and QA reads. It is an internal production artifact, not a rendered UI layer: never add a standalone visible `Living Cover Cue`, cue-card, cue-panel, node list, diagnostic label, or implementation-status panel to a viewer-facing proof unless a human explicitly approves that surface. Do not rely on a generic chapter map alone to prove that the episode feels authored.
- Every long-form Living Cover must also declare a packet-local `living_cover_ambient_effects_layer` before motion readiness. This artifact is separate from the cue map and the music integration contract: the cue map decides story beats, typography, and cascade moments; the ambient/effects layer decides source-integrated motion, micro-life, occlusion, and QA. Valid lanes include `none`, `minimal`, source drift/lighting, particles or dust, practical lights or screen glow, public-scene motion such as aircraft or vehicles, or a mixed episode-specific lane. `none` or `minimal` is allowed only with rationale and review reads; missing the artifact blocks motion readiness and rough assembly.
- Ambient/effects layers must preserve the approved source-art carrier. Record source/matte coordinate registration, foreground occlusion when effects pass behind scene elements, deterministic seeds or parameters, additive integration when adding a successor effect, browser sample QA, range-scrub QA for long proofs, and debug-overlay absence in viewer-facing output. Matte previews, route overlays, QA labels, implementation-status panels, and other diagnostic aids are review artifacts only; they must not render into the viewer-facing proof unless explicitly human-approved for a diagnostic surface.
- Person-operated or subject-originated ambient effects, such as camera flashes, phone flashes, flashbulbs, screen glints, hand signals, vehicle headlights, brake lamps, or equipment lights, must prove the core origin point sits on a visible subject/equipment surface, not merely inside a broad human-marked area. The ambient layer must record allowed subject-surface masks plus explicit exclusion masks for nearby architectural faces, blank walls, plants, vehicles/equipment shells, rail/text surfaces, or other surfaces that could catch glow but should not be the origin. Passing `inside_marked_region` is insufficient when the viewer-visible origin reads as an unlikely surface; record `subject_surface_origin_read`, `effect_origin_exclusion_read`, and episode-specific reads such as `people_standing_flash_origin_read` before rough proof or final assembly can advance. Camera flashes and flashbulbs require audited person/equipment hotspots or pixel-tight subject masks; broad line bands, balcony strips, walkway strips, high-jitter random sampling, or large halos that make the brightest source read as architecture are rough-proof blockers. Vehicle/equipment practical lights, including headlights and brake lamps, require a packet-local origin map with pixel-tight visible-surface masks, exact core coordinates, exclusion masks, and a zoomed calibration proof/contact sheet; QA must fail when light cores float near a vehicle, land on road/guardrail/text, or omit an expected visible vehicle/equipment origin. Glow may spill onto a slab, wall, deck, or road surface, but the visible core must remain on an audited subject pixel and the proof must include a zoomed contact sheet or equivalent visual evidence.
- Event-life ambient effects that imply ongoing public activity may use prewarmed schedules when a review asks for the scene to be active from the opening frame. Prewarmed effects must record the original timing, negative `start_seconds` or equivalent initial progress, preserved source origins, count preservation, and opening-frame browser proof. Do not fake activity by adding new people, new source-art elements, or debug overlays; record reads such as `balloon_effect_initial_frame_read`, `balloon_prewarm_origin_read`, and `balloon_count_preservation_read` when this pattern is used.
- Full-frame flash pulses are allowed only as secondary exposure reactions to validated source-locked flash events. They cannot replace person/equipment flash cores, cannot be sourced from broad regions, and cannot exceed a documented subtlety cap, defaulting to `0.075` alpha or lower unless a human-approved override names the episode/output and masking evidence. The ambient manifest must record the pulse source, maximum alpha, aggregate cap, end-screen cap, and reads such as `fullscreen_flash_pulse_read`, `flash_pulse_subtlety_read`, `flash_core_origin_preservation_read`, `audited_flash_origin_preservation_read`, and `end_screen_flash_pulse_suppression_read`.
- Person-operated camera flashes and flashbulbs default to `period_xenon_pop_with_video_bloom_v1`: a very short physical flash reference, a fast person-centered cream-white peak, a bounded warm halo, and a frame-scale review bloom that disappears within a few 24fps frames. Long half-second glows are stylized effects, not the default period behavior; they require `human_approved_stylized_long_flash_override_read` with the episode/output named. Record `period_camera_flash_behavior_read`, `xenon_pop_duration_read`, `video_bloom_decay_read`, `flash_core_peak_visibility_read`, `no_lingering_flash_dot_read`, and `per_hotspot_recycle_spacing_read` when camera flashes are scoped.
- Person-operated flash effects must be locally visible enough to justify any full-frame pulse. If a proof uses a whole-frame exposure reaction, the local flash core must remain visible on the audited subject/equipment pixel at the pulse peak, with a bounded halo and proof samples at event start, peak, short bloom, and post-decay. Record `flash_core_visibility_read` or `flash_core_peak_visibility_read`, `flash_duration_visibility_read` or `xenon_pop_duration_read`, `global_pulse_local_core_coupling_read` or `global_pulse_peak_coupling_read`, `flash_halo_boundary_read`, and `flash_not_strobe_read`; a global pulse without a visible local source is a rough-proof blocker.
- Every long-form Living Cover must declare a packet-local `music_integration_contract` before rough assembly and before rough-proof `keep`. This artifact is separate from the ambient/effects layer and from final audio mastering: it records the approved music sources, series/episode contract, intro/outro timing, voice-start offset, caption/chapter/story-time retiming, end-screen music handoff, VO-to-outro blend plan, level QA, rights/Content ID notes, regression reads, and any human-approved waiver. A voice-only or visual-only rough proof without this contract is `review_ready_blocked_missing_music_contract` and cannot advance to rough-proof `keep`, final render, final assembly, publish readiness, upload prep, or release.
- Challenger is the default series precedent for long-form music unless a future episode records a human-approved alternate contract or waiver. The default contract is music-only intro when the approved intro source has a lead-in, voice starts after the intro lead-in, a 2-second intro fade tail under the opening voice when using the Challenger pattern, full outro music through the end-screen window, `subtle_tail_outro_v1` for the final VO-to-outro transition, and timing model support for shifted captions, chapters, and story-time anchors.
- `subtle_tail_outro_v1` means the approved full outro source enters only under the last 1-2 seconds of VO at a low bed level, cannot crowd or mask the final spoken line, reaches target level only after VO ends, continues without restarting, and carries the end-screen window. A low-level bridge, motif loop, or proxy source may be supplemental texture only; it cannot substitute for the approved full outro source.
- Broad actual-outro prelap models, including 5-second/high-gain fades or target-at-voice-end behavior, are not the default contract. They require a human-approved episode override naming the output, rationale, exact timing/gain values, masking evidence, and affected gates; otherwise final render and publish-readiness validators must fail them even when broad VO/outro reads are present.
- Final render scripts must hard-fail when the active proof/final manifest lacks a non-stale packet-local music mix with passing `vo_outro_blend_plan_read`, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_transition_review_sample_read`, `outro_entry_level_match_read`, `outro_under_vo_masking_read`, `outro_target_after_voice_read`, `outro_prelap_source_read`, `outro_prelap_start_read`, `outro_no_restart_at_voice_end_read`, `outro_source_continuity_read`, and `music_contract_regression_read`. Broad reads such as `full_outro_music_read`, `end_screen_music_handoff_read`, or `audio_level_mix_read` are not substitutes for the VO/outro transition gate.
- Music-only intros must start in a readable settled rail state. When `storyTimeAt(audioTime)` clamps to `0` before voice start, do not let the first chapter stay at transition phase `0`; the first active title, summary, active panel, and relevant context rows must be visible at `t=0`, mid-intro, and voice start unless a human-approved cold-open override scopes a different treatment. Rough proofs must record `intro_rail_readiness_read`, `intro_active_title_read`, `intro_summary_legibility_read`, `intro_context_readability_read`, and `intro_transition_completion_read`.
- Therac/Challenger regression rule: do not use an under-opening-voice bed plus a short 15-second tail when the user request or series precedent says to match Challenger. Use music-only intro, voice offset, fade tail, and full outro; if an episode intentionally differs, record the alternate contract and human rationale.
- A `no_music_or_temp_music_waiver_read` can pass only when a human-approved waiver names the episode/output, gives the rationale, states the affected proof/final/publish gates, and records the next required music action. Missing music is otherwise a blocker, not an implicit temporary state.
- Use [/Users/mike/CascadeEffects/apps/web/brand](/Users/mike/CascadeEffects/apps/web/brand) as the visual source of truth before making new visual choices.
- Before changing or generating a long-form Living Cover backplate for an episode with an existing baseline, load the episode visual-system baseline index and the episode baseline doc. Treat the baseline as the active episode visual truth unless a human explicitly approves a deviation. Record the baseline path, baseline status, active source-art path/hash, source manifest path/hash, inherited required reads, and any deliberate deviation in the visual-system plan or source-art manifest. Do not import known superseded artifacts as active source art.
- For Living Cover visual-system and rough-assembly work, use `living_cover_system_v1` from [/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md](/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/references/living_cover_system_spec_v1.md). Default to `fixed_16x9_right_rail_v1` with human-reviewed overrides only.
- For first-eight long-form episodes, the active right-rail content model is `rolling_caption_anchor_v1` and the active caption display model is `rolling_rail_caption_window_v1`. Preserve the fixed rail geometry (`760px` width, `52px` right/top/bottom inset), remove the old previous/upcoming context list, suppress top title/chapter copy for caption-only review unless a minimal anchor is explicitly enabled, and place the rolling caption window in the middle/right of the rail. Use `script_locked_chunk_split_v1`, `hidden_in_render_mode`, and `reviewed_cue_map_spans_only`.
- For Living Cover captioning, use `living_cover_captioning_process_v1` from the Living Cover system spec. Captions are required by default: every Living Cover visual-system, rough-proof, final-assembly, and publish-readiness packet must record caption provenance, caption QA, and `caption_output_model: dual_visible_rail_and_youtube_vtt_sidecar` unless a human-approved waiver is recorded.
- Living Cover caption text must be script-locked: the locked narration script is the only allowed source of visible caption words. ASR, WhisperX, VTT, and SRT artifacts may supply timing only. Rough-proof, final-assembly, and publish-readiness advancement is blocked unless `caption_text_matches_script_read`, `caption_alignment_coverage_read`, and `caption_asr_text_not_used_read` are present and passing.
- Rolling rail captions must be deterministic from audio/render time: split long script-locked cues into 1-2 line display chunks, precompute fixed layout, map `audio.currentTime` or `window.__setRenderTime(time)` to one `translateY`, expose `window.__railCaptionStateAt(time)`, and animate only opacity, transform, and highlight color/alpha. Free-running caption scroll animations, layout jumps, font-size changes, heavy caption panels, badge/box/glow/karaoke/progress/timecode treatments, and out-of-rail caption text block rough-proof advancement.
- Rolling key-phrase highlights must come from reviewed Living Cover cue-map spans only. Each reviewed span records phrase text, normalized script token range, timing window, sampled highlight color, fade-in/out duration, and review status; do not auto-select unreviewed phrases as final, and suppress highlight rendering when reviewed spans are missing.
- Living Cover rail copy must be episode-specific viewer-facing language. Active rail data must record `stale_cross_episode_label_read`, and stale cross-episode labels, internal production labels, or generic web-app labels block rough proof, final assembly, and publish readiness until repaired.
- `fixed_16x9_right_rail_v1` is a rail-only text preset by default. All viewer-facing story text, chapter text, effect/cascade wording, captions, and end-screen wording must live inside the fixed right rail unless a human-approved visual-system override explicitly scopes another text surface. Standalone left-side chapter slates, effect cards, lower thirds, cue cards, end labels, and other out-of-rail text surfaces are `tighten`/`reject` blockers.
- Ordinal-only chapter labels such as `CHAPTER 01`, `PART 1`, or `SECTION 03` are not valid viewer-facing Living Cover copy. Chapter labels and active titles must be semantic, episode-specific hooks; numbering may exist only in internal manifests or human-approved diagnostic views.
- Living Cover end-screen holds mean static YouTube target geometry, not identical full-frame pixels. Background motion policy must be explicit: continuous ambient motion may continue behind the static overlay only when `continuous_ambient_end_screen_preservation_read` and `youtube_target_geometry_static_read` pass. The default long-form template is the Challenger/Therac titleless three-target template `challenger_titleless_end_screen_overlay_on_living_cover_v1`: left video `[78,382,758,765]`, right video `[1162,382,1842,765]`, and center subscribe `[814,429,1106,721]`. Any one-video, rectangular subscribe, title-bearing, or ad hoc geometry needs a human-approved episode override and must record the reason. Under `rolling_rail_caption_window_v1`, captions continue upward at the approved transition, then caption text and highlights fade to zero before the YouTube target-geometry window; the default caption container has no blur, fill, or background treatment. Chapter, context, caption, cue, and rail text must be fully suppressed in the YouTube end-screen window unless a human-approved title policy explicitly allows viewer-facing end-screen text. Faintly faded text is an artifact, not a pass; record `caption_end_screen_rollout_read`, `end_screen_text_artifact_read`, `viewer_text_suppression_read`, and `youtube_end_screen_template_read`.
- Once an approved Living Cover backplate exists, every rough, final, and publish-readiness manifest must carry `end_screen_palette_contract` before advancement. The contract must name the approved backplate path/hash, use `palette_source: sampled_episode_backplate` or a named human-approved override, record sampled/harmonized target colors for video target fill, target border, subscribe ring, muted rail text, and small accents, and pass `end_screen_palette_contract_read`, `end_screen_target_fill_palette_read`, `end_screen_target_contrast_read`, `rail_panel_palette_read`, `source_integrated_panel_color_read`, and `no_cross_episode_default_palette_read`. Missing, stale, copied Challenger/default, or non-passing palette evidence blocks rough-proof `keep`, final render, publish readiness, upload prep, and YouTube action.
- Final MP4 renderers must render from the current kept HTML proof, not an older successor-builder script. Render manifests must record `source_html_proof` path/hash, `current_kept_proof_render_source_read`, audio encode/copy policy, full decode, duration, codec, dimensions, fps, caption sidecars, visible rail caption burn-in, and downstream gate state.
- Episode bootstrap creates a stable lifecycle review surface immediately. The local packet lives under the episode production tree and includes `review.html` from inception onward; the production URL is `https://cascadeeffects.tv/reviews/publish-readiness/{episodeId}`. The initial manifest has `lifecycle_stage: "inception"`, no YouTube video, all upload/publish/visibility locks false, and placeholder blockers until real proof/final assets exist.
- The lifecycle `review.html` must continue to exist in `in_progress` states before final assembly `keep`. It may embed the latest reviewable proof or final as a current review artifact, but it must label the current gate, show blockers, and keep `publish_ready`, `youtube_upload_ready`, `public_release_ready`, `may_youtube_action`, and `upload_performed` false.
- Publish-readiness packages must use an HTML-first local review surface. The primary local human review artifact is `review.html`, with visible package-local media references for the final MP4, caption sidecar, thumbnail candidate, QA frames, metadata/chapter preview, blocker list, and upload-lock status. Copy or stage those media assets into the publish-readiness packet so the page is portable. The canonical local review URL must be served through a byte-range-capable local review server, usually `http://127.0.0.1:<port>/review.html`, so native MP4 controls can scrub to arbitrary times. A `file://` page may exist as trace evidence, but it cannot satisfy publish-readiness review by itself. Markdown may exist only as a secondary note; it must not be the primary review artifact.
- The cascadeeffects.tv lifecycle review may be published at inception without video. After a reviewable proof/final exists, use an unlisted YouTube upload in the Cascade of Effects channel as the heavy video host; never upload final MP4, MOV, M4V, or other large video files to Vercel/Blob. The remote review package may upload only the normalized manifest and small evidence assets such as metadata, captions, thumbnail candidate, QA frames, and transition samples. Record the unlisted YouTube receipt/status, `youtube_unlisted_review_upload_read`, `youtube_unlisted_review_privacy_read`, `youtube_embed_permission_read`, `youtube_embedded_playback_ready_read`, `remote_review_url`, `remote_review_manifest_read`, and `remote_review_large_video_upload_block_read` when the video-backed remote review is published. An unlisted video with YouTube embeds disabled is a blocker, not a warning, because cascadeeffects.tv cannot play it inline.
- For Living Cover generated raster, generated video, source-art, motion-readiness, rough-proof, final-assembly, and publish-readiness work, record `generation_provenance` for every generated visual carrier. The record must name the tool, model when known, confidence, generation mode, output/final asset paths and hashes, prompt path/hash, init or reference image paths when applicable, and a short provenance note.
- ImageGen is the primary source-art generator for long-form Living Cover imagery. Each long-form episode should produce ImageGen-generated `1920x1080` source-art candidates by default, using episode references, brand contracts, and visual-system constraints as inputs. Sourced archival stills or video frames are reference evidence, not the default production backplate.
- Long-form video assets must not use Paper Architecture as the active visual style. The default long-form illustration lane is `cascade-ink-lit-photoreal-v1` or an episode-specific source-preserving/photoreal public-scene carrier. `cascade-paper-architectures-ink-lit-v1`, folded-paper/foam-core aircraft or building models, paper planes, cream paper forms, paper-cutaway tableaux, and other Paper Architecture resemblance cues are blocked for long-form source-art prompts, candidates, rough proofs, finals, cover frames, in-video end screens, and thumbnail-derived backplates. Record `video_visual_style_scope_read` and `paper_architecture_visual_style_read` before source-art `keep`; Paper Architecture resemblance is `reject`.
- Generated Living Cover source-art backplates must use the Codex `imagegen` skill with built-in `image_gen` unless a later human-approved plan explicitly chooses another generator. Local Python, HTML, CSS, SVG, canvas, FFmpeg, or Playwright composition may package, resize, make previews, mask, QA, or assemble approved raster assets, but must not create the source-art backplate itself. Manifests must record `imagegen_skill_read`, `source_art_generation_tool_read`, `local_rendered_backplate_read`, and `source_art_workspace_copy_read`.
- A sourced-raster, archival-frame, deterministic-composition, or non-ImageGen backplate can be active source art only when a human-approved exception names the episode, reason, source paths, affected outputs, rights/source-risk read, and why ImageGen is insufficient for that gate. Without that exception, sourced frames remain `reference_only` or `diagnostic_only` and cannot advance to source-art `keep`, motion readiness, rough assembly, final render, package use, or publish readiness.
- ImageGen output must be measured against episode-specific historical accuracy before source-art promotion. The source-art gate must define the real-world visual facts the image is trying to represent, cite the reference basis used for judging them, and record `historical_accuracy_read`, `source_reference_alignment_read`, `public_anchor_geometry_read`, and an episode-specific read such as `hyatt_atrium_architecture_read` or `launch_pad_scene_read`. A candidate that invents, removes, relocates, or visually contradicts episode-central architecture, equipment, public anchors, or period setting is `tighten` or `reject` even if it is aesthetically strong.
- Long-form Living Cover source art has one default episode-backplate lane: `cascade-ink-lit-photoreal-v1` or an episode-specific source-preserving/photoreal public-scene carrier. Paper Architecture may appear only in website assets, YouTube channel-level brand assets, and CascadeEffects.tv website thumbnail-gallery images. It must fail style preflight when it appears in an active long-form visual-system plan, source-art prompt, source-art manifest, rough proof, final, cover frame, in-video end screen, or thumbnail candidate.
- Public-scene, institutional, human/tableau, crowd, or event-based Living Cover source art should include anonymous human presence unless the visual-system plan records a human-presence waiver. Human figures must be unrecognizable: no face-forward close-ups, identifiable likenesses, celebrities, public officials, victim portraits, or generated faces that could read as a real person. Record `human_presence_read` and `no_recognizable_faces_read`; a missing required human presence is `tighten`, and a recognizable face is `reject`.
- Long-form Living Cover source art must avoid default foreground administrative props. Clipboards, binders, folders, paperwork stacks, legal pads, and generic desk evidence in the dominant foreground are `tighten` or `reject` unless a human-approved episode exception names the exact object, explains why it is mechanism-critical, and records `foreground_admin_prop_exception_read: pass`. Prefer implied action and anticipation: people about to act, public-scene attention, open thresholds, active equipment, restrained screen glow, practical lights, weather surfaces, crowd density, machinery readiness, and layered depth that gives the later ambient/effects layer something credible to animate.
- Photoreal/source-preserving Living Cover proofs must not draw procedural cyan signal lines, diagnostic traces, generated UI paths, connector lines, or other canvas/SVG overlays over the source-art backplate unless a human-approved visual-system plan explicitly scopes that overlay. Record `procedural_signal_overlay_read` and `ambient_line_artifact_read`; both must pass before rough proof, final render, or publish readiness can advance.
- Living Cover rail panel and backlight colors must be source-aware. The active rail panel, end-screen target fill, muted rail text, and small accent colors must be sampled from or harmonized with the episode's approved backplate while preserving caption/title contrast. Challenger's dark navy rail worked because it matched a night-sky/launch-pad backlight; do not reuse that navy as a default for Therac or future non-night-sky episodes. Record `end_screen_palette_contract`, `rail_panel_palette_read`, `source_integrated_panel_color_read`, and `no_cross_episode_default_palette_read`; a fixed cross-episode panel or target color is a `tighten`/`reject` blocker unless a human-approved override names the episode, reason, affected output, and affected gates.
- Living Cover and long-form source-art treatments should preserve the active approved source-art lane. Avoid broad full-frame dark translucent overlays by default; prefer localized soft readability treatments behind rail, title, or caption regions when needed, and record `full_frame_dark_overlay_read` plus `localized_readability_treatment_read`.
- Under `fixed_16x9_right_rail_v1`, readability treatment must not become a full-height opaque right-column panel below the active scene text. The active panel may carry its own fill, and captions may use a localized lower-rail treatment only while captions are visible, but the context/list region should leave the source image visibly present unless a human-approved episode override says otherwise. Record `rail_backlight_scope_read`, `right_rail_opacity_balance_read`, `context_region_source_visibility_read`, and `caption_softener_scope_read`; excessive darkening below the active scene text is a `tighten` blocker.
- Reuse approved existing assets before creating new ones: long-form audio, existing one-per-episode Shorts, outro song/Paper Architecture music motif, non-Paper-Architecture brand illustrations when explicitly approved for video, captions, chapters, and packaging.
- Treat existing Shorts as the first long-form bridge and MVP minimum. Do not require a new 6-10 Short batch unless a later production plan explicitly scopes it.
- Identify 6-10 Short candidates for each full episode when strategy or packaging work is in scope, but route all new or revised Shorts through the Shorts production skill.
- Block static-thumbnail videos, one unchanging loop for the full runtime, waveform-only exports, unrelated generic AI animation, and long intros before the substance begins.
- For photoreal, source-preserving, or non-Paper-Architecture brand-illustration long-form proofs, the core visual carrier must be generated or approved raster/source artwork. HTML, CSS, SVG, canvas, and other procedural code may only provide proof-player shell, timing, captions, deterministic typography, safe-zone layout, masks, transforms, and layer compositing over approved visual assets unless the user explicitly asks for a code-native diagnostic mockup.
- Treat CSS/SVG/canvas-drawn public anchors, evidence objects, Paper Architecture scenes, evidence terraces, or living-cover backgrounds as `diagnostic_only`; they cannot become the active visual plan, motion-readiness input, rough-assembly baseline, thumbnail, or publishable package asset.
- If Paper Architecture source art, titles, chapter cards, hero surfaces, package art, or proof visuals appear inside the long-form video workflow, record `paper_architecture_visual_style_read: reject` and stop advancement. Paper Architecture material QA applies only in the website, YouTube channel-brand, and CascadeEffects.tv website thumbnail-gallery workflows.
- When surface texture starts creeping into long-form source art, record `texture_detail_creep_read: pass|tighten|reject`. Repairs must preserve the selected non-Paper-Architecture carrier and must ban visible speckle, grit, sandy surface, fiber clumps, mottled background texture, AI shimmer, rough plaster, fabric-like weave, noisy shadows, over-detailed micro-surface, and texture that competes with source readability.
- A proof, source-art candidate, thumbnail, package asset, or motion-readiness candidate with `texture_noise_read: tighten` or `texture_noise_read: reject` cannot advance to `keep`, rough assembly, or refreshed `long_form_living_cover_motion_readiness` until repaired and re-reviewed.
- Cyan cause-and-effect cues in long-form source art must read as dry vellum signal traces, flat paper ribbons, or small suspended signal markers, never water. Prompts with cyan path cues must include `dry cyan vellum signal trace, no water/waterfall/river/stream/canal/channel/liquid spill/glowing watercourse`; record `waterfall_read: pass|tighten|reject`, and only `pass` can advance to `keep`, rough assembly, motion readiness, or MP4 render.
- Episode-specific long-form source art must not reuse homepage-hero folded mountain, folded terrace, generic cascade waterfall/terrace, title-bearing brand-hero staging, or Paper Architecture treatment when the episode calls for a real public scene anchor. If the asset is for Challenger launch-pad coverage, the public anchor must be a reference-anchored Challenger/LC-39 launch-pad scene in a non-Paper-Architecture video style.
- Challenger launch-pad source-art candidates must record `launch_pad_scene_read: pass|tighten|reject`, `website_hero_artifact_read: pass|tighten|reject`, and `reference_anchor_read: pass|tighten|reject`. Any `tighten` or `reject` value in these fields blocks `keep`, motion readiness, rough assembly, package use, or MP4 render even when `texture_noise_read` and `waterfall_read` are `pass`.
- Challenger launch-pad source art must also record `brand_signal_artifact_read: pass|tighten|reject` and `pad_hardware_authenticity_read: pass|tighten|reject`. Do not prompt or accept visible brand-signal objects on launch hardware: no cyan flags, tabs, ribbons, tape scraps, stickers, labels, UI markers, standalone coral/orange blocks, cubes, warning tabs, or random colored accents. Any `tighten` or `reject` value in these fields blocks `keep`, motion readiness, rough assembly, package use, or MP4 render.
- Public release is manual unless a separate publish skill or explicit user instruction owns the action.

## Artifact Safety And Variant Integrity

Artifact-safety reads are hard gates. Any `tighten` or `reject` in stream integrity, source provenance, historical/source-reference accuracy, freeze/speed, end-screen stability, music integration, text/material policy, or source-art cleanliness blocks `keep`, rough assembly, final assembly, package use, and publish readiness until repaired.

Every proof, MP4 render, publish-readiness package, channel-trailer candidate, upload, update, or delete must pass the executable output contract harness before it can advance. The manifest must declare `production_contract.contract_id` and `production_contract.intent`; valid intents are `repair`, `successor`, and `experiment`. Repairs require an explicit `allowed_delta` contract naming allowed time spans, pixel regions, stream changes, unchanged hashes, and frame-diff expectations. Use:

`node scripts/validate_cascade_effects_output_contract.mjs --manifest PATH --intent repair|successor|experiment --contract-id first-eight-longform-v1|channel-trailer-v1 --json`

The validator receipt is the gate artifact. Render/package/upload scripts must fail closed without a passing receipt. YouTube upload, description update, or delete also requires an action-specific receipt with `youtube_action_allowed: true` plus explicit human approval for that exact action. `not_applicable` and legacy `tighten` exceptions are allowed only when the contract registry declares the read and its required dependent pass reads.

Long-form proof and final manifests must record every rendered media source by path, role, SHA-256, stream count, codec, duration, and decode status. Use `pass|tighten|reject|not_applicable` for read values, and do not treat `not_applicable` as a blocker when the packet has no rendered stream or no predecessor to compare against. Final MP4s must record `full_decode_read`, plus `visual_freeze_read`, `proof_speedup_read`, and `post_change_regression_read` when they are successors or variants of an earlier proof/final.

For narrow variants, preserve the unchanged stream and prove it by hash: audio-only changes must copy or preserve the video stream and record `video_stream_copy_read`; visual-only changes must copy or preserve the audio stream and record `audio_stream_copy_read`. If the unchanged stream cannot be copied exactly, the manifest must explain the unavoidable re-encode and include a targeted regression comparison.

Creative pacing reads are review reads, not automatic blockers. If a long-form cold open or montage exists, record `cold_open_settle_read`; it should confirm that high-energy opening motion settles before the first stable story or layout state. Human review may still mark the pass `tighten`.

## Phase Gates

Every phase starts with `may_advance: false`. A phase may move from `review_ready` to `keep` only after human review. Valid human dispositions are `keep`, `tighten`, `reject`, and `defer`.

If approval is ambiguous, keep `may_advance: false`, set `disposition: blocked`, and name the blocker.

Gate choreography is strict: episode bootstrap opens the stable lifecycle review URL and local lifecycle `review.html` only, not upload readiness. `keep` on an HTML rough proof may open final render only; `keep` on final assembly may open publish readiness only. Before final-assembly `keep`, the same review surface may be refreshed as `lifecycle_stage: "in_progress"` with the current review artifact and blockers visible, but it must not record keep or open upload. After final-assembly `keep`, the next production action is to refresh the HTML-first publish-readiness package at the same stable review ID. YouTube upload, publish, schedule, and visibility actions remain blocked until a publish-readiness package exists, the package receives human `keep`, and a human gives explicit approval for the upload or visibility action.

First-eight rail redesign gate rule: Challenger, Therac, Hyatt, Tacoma, Piltdown, Titanic, Semmelweis, and 737 MAX must each receive a refreshed rough-assembly rail proof or blocked rough-assembly rail packet using `rolling_caption_anchor_v1` before final assembly, publish readiness, or YouTube upload gates are trusted again. Challenger, Therac, and Hyatt publish/final-facing legacy rail surfaces are superseded; Tacoma refreshes its rough-review-ready proof; Piltdown and Titanic pause final assembly until successor rough proofs are kept; Semmelweis and 737 MAX move into rough assembly with the new rail only after their current prerequisite keeps. This is not a default source-art rollback because the rail footprint is unchanged; revalidate right-rail safe space and reopen source art only if that revalidation fails.

Missing music contracts are gate blockers: rough proofs without `music_integration_contract` or a passing `no_music_or_temp_music_waiver_read` must remain `review_ready_blocked_missing_music_contract`, even if visuals, captions, and ambient/effects reads are otherwise review-ready.

### 1. Inventory Gate

Take stock episode by episode:

- long-form audio status
- existing Short status and whether it can serve as a Related Video bridge
- outro/music status, including Paper Architecture motif availability and rights notes
- brand illustration, design-system, and package assets available from `/Users/mike/CascadeEffects/apps/web/brand`
- captions, chapters, titles, thumbnails, descriptions, and end-screen status
- rights, Content ID, source, or approval blockers
- next action for each episode

Human review chooses which episode enters long-form video production first.

### 2. Episode Package Gate

Confirm:

- long-form audio is current and usable
- frontier-model script critique exists for the exact script revision used by the audio render
- required critique changes are integrated, or deferred with explicit rationale and human approval
- explicit human script approval for audio render exists after critique integration
- audio source integrity proves the long-form audio was rendered from the approved post-critique script revision
- episode mechanism, promise, chapter spine, and CTA path are clear
- the episode answers: what changed, who failed to recognize the change, and how the system converted that blindness into consequence
- existing Short bridge, playlist path, or next-video path is identified when available
- default 40-minute spine is mapped:
  - `0:00-0:20` cold open with the strongest idea, contradiction, or question; no housekeeping
  - `0:20-0:40` micro-title or identity hit
  - `0:40-3:00` episode promise and cascade framing
  - `3:00-34:00` 4-6 chapters with clear turns or questions
  - `34:00-38:30` synthesis
  - `38:30-39:15` CTA and next path
  - `39:15-40:00` outro song plus end-screen window
- non-40-minute episodes may scale timing proportionally, but must preserve the same functional beats
- 6-10 Short candidates are identified when a Shorts expansion is scoped: central thesis, surprising details, emotional or philosophical turns, visual concept or cascade map, and direct start-here bridge

Block if the mechanism is vague or if the episode package cannot support a chaptered video essay.

### 3. Visual System Gate

Approve the episode's living-cover direction against the brand contracts in `/Users/mike/CascadeEffects/apps/web/brand`.

The plan must include:

- episode visual-system baseline reference when one exists, including baseline path, baseline status, active source-art path/hash, source manifest path/hash, inherited required reads, known superseded artifacts, and explicit deviation notes
- visual carrier declaration for each proof direction. Default carrier type is `generated_raster_source_art` produced through Codex `imagegen`; `sourced_raster_source_art`, `hybrid_raster_source_art`, or `deterministic_composition_over_approved_raster` require a named human-approved source-art exception before they can be active production backplates.
- video visual style scope declaration. Default to `cascade-ink-lit-photoreal-v1` or an episode-specific source-preserving/photoreal public-scene carrier. Paper Architecture resemblance blocks source-art generation, source-art `keep`, motion readiness, rough proof, final render, publish readiness, cover-frame use, in-video end-screen use, video-thumbnail use, and package use.
- generation provenance for every generated raster, generated video, source-art, motion carrier, or deterministic composition carrier, including `generation_tool_provenance_read`
- historical/source-reference accuracy criteria for ImageGen candidates, including canonical visual facts, allowed abstraction, hard mismatch blockers, source/reference paths or URLs, and required reads such as `historical_accuracy_read`, `source_reference_alignment_read`, `public_anchor_geometry_read`, and any episode-specific architecture/equipment read. Reference archival media should be cited as judgment evidence unless a human-approved source-art exception makes it the carrier.
- composition and prop-hygiene criteria for ImageGen candidates, including `foreground_admin_prop_read`, `implied_action_anticipation_read`, and `ambient_affordance_read`; foreground clipboards, binders, folders, paperwork stacks, legal pads, or generic desk evidence block source-art `keep` unless a human-approved exception records why the exact object is necessary and not the dominant visual idea
- `living_cover_system_version`, `rail_preset_id`, `rail_content_model_id`, `caption_display_model`, `caption_window_role`, `caption_window_treatment_model`, `caption_blur_scope`, `caption_highlight_source`, `caption_palette_source`, and `override_status` when the plan scopes a Living Cover proof
- `captioning_process_version`, `caption_required`, `caption_output_model`, `caption_text_source`, `caption_timing_source`, and caption source/provenance expectations; if the locked narration script, timing source, or script/audio alignment gate is missing, record the blocker before rough assembly
- `texture_noise_read: pass|tighten|reject` for every generated/source-art proof direction, reviewed at desktop and YouTube-preview scale
- readability strategy for rail, title, and caption regions, including `full_frame_dark_overlay_read` and `localized_readability_treatment_read` when overlays or readability treatments are used
- end-screen palette strategy once a backplate direction is selected, including `end_screen_palette_contract`, approved backplate path/hash, sampled or human-approved override source, derived target fill/border/subscribe/text/accent colors, contrast reads, and `no_cross_episode_default_palette_read`
- rolling caption rail strategy, including `rail_content_model_read`, `caption_display_model_read`, `caption_display_chunking_read`, `review_chrome_policy_read`, `highlight_render_policy_read`, `caption_window_role_read`, `caption_window_treatment_read`, `caption_highlight_source_read`, `caption_palette_source_read`, `old_context_rows_absence_read`, `minimal_anchor_read`, `rolling_caption_behavior_read`, `rolling_caption_state_hook_read`, `caption_scroll_smoothness_read`, `caption_window_fade_mask_read`, `caption_window_transparency_read`, `caption_key_phrase_span_read`, and `caption_highlight_fade_read`
- rail backlight/source visibility strategy, including `rail_backlight_scope_read`, `right_rail_opacity_balance_read`, `context_region_source_visibility_read`, `caption_softener_scope_read`, `caption_window_treatment_read`, `end_screen_target_fill_palette_read`, and `end_screen_target_contrast_read` so localized readability treatment does not become a full-height opaque rail column below the active scene text and the YouTube targets are episode-local
- scene-specific reads such as `launch_pad_scene_read`, `hyatt_atrium_architecture_read`, `website_hero_artifact_read`, `reference_anchor_read`, `video_visual_style_scope_read`, and `paper_architecture_visual_style_read` when an episode visual must be anchored in a recognizable public scene rather than the generic brand hero or Paper Architecture grammar
- a dedicated `living_cover_cue_map` artifact, with `living_cover_cue_map_read`, `chapter_cue_coverage_read`, `typography_cue_read`, `effect_map_cue_read`, `source_safe_motion_read`, `cue_no_diagnostic_overlay_read`, `cue_map_internal_artifact_read`, and `visible_cue_overlay_read` planned before rough assembly
- a viewer text-surface policy for `fixed_16x9_right_rail_v1`, with `viewer_text_surface_inventory_read`, `right_rail_text_boundary_read`, `out_of_rail_text_read`, `ordinal_chapter_label_read`, and `end_screen_text_boundary_read` planned before rough assembly
- a dedicated `living_cover_ambient_effects_layer` artifact, with `ambient_effects_plan_read`, `ambient_effect_lane_decision_read`, `source_plate_matte_registration_read`, `foreground_occlusion_read`, `effect_layer_source_safety_read`, `deterministic_ambient_read`, `additive_effect_integration_read`, `debug_overlay_absence_read`, `ambient_effect_browser_sample_read`, and `range_scrub_effect_review_read` planned before motion readiness; subject-originated effects must also plan `subject_surface_origin_read`, `effect_origin_exclusion_read`, and the episode-specific origin/exclusion reads needed for that scene
- opening-frame activity and exposure-pulse reads when scoped by review, including `balloon_effect_initial_frame_read`, `balloon_prewarm_origin_read`, `balloon_count_preservation_read`, `fullscreen_flash_pulse_read`, `flash_pulse_subtlety_read`, `flash_core_origin_preservation_read`, `audited_flash_origin_preservation_read`, and `end_screen_flash_pulse_suppression_read`
- local flash visibility reads when a full-frame pulse is present, including `period_camera_flash_behavior_read`, `xenon_pop_duration_read`, `video_bloom_decay_read`, `flash_core_peak_visibility_read`, `flash_origin_precision_preservation_read`, `flash_halo_boundary_read`, `global_pulse_peak_coupling_read`, `no_lingering_flash_dot_read`, `per_hotspot_recycle_spacing_read`, `irregular_cadence_read`, and `flash_not_strobe_read`; older long-glow reads require a human-approved stylized override
- a dedicated `music_integration_contract` artifact, with `music_integration_plan_read`, `series_music_contract_read`, `approved_music_source_read`, `intro_music_contract_read`, `voice_start_offset_read`, `caption_timing_shift_read`, `full_outro_music_read`, `end_screen_music_handoff_read`, `vo_outro_blend_plan_read`, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_transition_review_sample_read`, `outro_entry_level_match_read`, `outro_under_vo_masking_read`, `outro_target_after_voice_read`, `outro_prelap_source_read`, `outro_prelap_start_read`, `outro_no_restart_at_voice_end_read`, `outro_source_continuity_read`, `audio_level_mix_read`, `music_rights_read`, and `music_contract_regression_read` planned before rough assembly; use `no_music_or_temp_music_waiver_read` only for explicit human-approved exceptions
- intro rail readiness for music-only lead-ins, with `intro_rail_readiness_read`, `intro_active_title_read`, `intro_summary_legibility_read`, `intro_context_readability_read`, and `intro_transition_completion_read` planned before rough assembly; for `rolling_caption_anchor_v1`, treat legacy title/summary/context reads as minimal-anchor or removed-context compatibility reads rather than permission to render the old context stack
- ambient motion base layer or reviewed `none|minimal` lane with rationale
- structured visual shifts every 4 to 8 minutes
- chapter/title cadence expressed through right-rail transitions unless a human-approved override scopes another surface
- key phrase typography every 1 to 2 minutes inside the rail or as non-textual source-safe visual behavior
- 4 to 6 cascade diagrams or effect-map moments expressed as rail behavior or non-textual source-safe motion unless a human-approved override scopes a visible text panel
- brand illustrations where they clarify the episode
- outro song and end-screen timing, with a 15 to 30 second outro and a final 5 to 20 second end-screen window
- any cold-open or montage pacing intent, with `cold_open_settle_read` planned as a review read when applicable

Reject visuals that ignore the brand contracts, use unrelated generic AI imagery, fail the episode's historical/source-reference accuracy criteria, make the video feel abandoned, default to foreground clipboards/binders/folders/paperwork as the visual anchor, lack implied action or ambient/effects affordance, use Paper Architecture resemblance as a video asset style, carry high-frequency speckle/noise/grain/grit/sandy texture, rely on broad dark veils instead of localized readability treatments, or use CSS/SVG/canvas/procedural art as the core scene carrier without explicit diagnostic-only scope.

Run motion-readiness review after a human `keep` on the visual system direction and before any rough assembly proof. If multiple visual directions are under review, only the selected `keep` direction can enter motion readiness.

### 4. Rough Assembly Gate

Review a full or representative proof with:

- voice audio
- approved music integrated according to the packet-local `music_integration_contract`, or a human-approved no-music/temp-music waiver that records the next required action
- ambient background
- fixed `1920x1080` Living Cover canvas and right-rail preset when using `living_cover_system_v1`
- `rolling_caption_anchor_v1` rail content over `fixed_16x9_right_rail_v1`: top title/chapter copy suppressed by default for caption-only review, no previous/upcoming context list, and a middle/right rolling caption window using `transparent_caption_mask_only_v1` with no blur, fill, or container background
- deterministic rolling rail captions generated from locked script text and approved timing provenance when using `living_cover_captioning_process_v1`; ASR/WhisperX/VTT/SRT text remains timing-only
- a packet-local `living_cover_cue_map` tying chapter shifts, typography cues, and effect-map moments to source-safe proof behavior; the cue map must stay internal unless a human-approved visual-system plan explicitly authorizes a visible cue surface
- a packet-local `living_cover_ambient_effects_layer` declaring the active ambient/effect lanes, source/matte safety, deterministic parameters, additive integration policy, browser/range QA, and any reviewed `none|minimal` rationale
- a packet-local `music_integration_contract` declaring the active music lane, approved sources, intro/outro policy, voice-start offset, caption/chapter/story-time retiming, final VO-to-outro blend plan, subtle-tail timing and gain fields, level/rights checks, transition review sample, and regression checks
- right-rail chapter/title cadence, not standalone out-of-rail chapter cards unless explicitly approved
- typography cues inside the rail or as non-textual source-safe visual behavior
- diagrams or effect maps that do not put viewer-facing text outside the rail unless explicitly approved
- brand illustration treatments
- temporary outro and end-screen area
- packet-local `end_screen_palette_contract` proving the YouTube target fill, target borders, subscribe ring, muted rail text, and small accents are sampled from or harmonized with the approved backplate; missing/stale/default palette evidence keeps the rough proof blocked even if geometry and caption rollout pass
- render integrity reads for source provenance, stream count, codec, duration, hash recording, and `full_decode_read`
- motion regression reads: `visual_freeze_read`, `proof_speedup_read`, and `post_change_regression_read` for successor proofs
- right-rail copy sanity reads, including `stale_cross_episode_label_read`, to prove labels are episode-specific and not stale from another episode
- text-surface boundary reads, including `viewer_text_surface_inventory_read`, `right_rail_text_boundary_read`, `out_of_rail_text_read`, `ordinal_chapter_label_read`, and `end_screen_text_boundary_read`, to prove visible text is rail-contained and semantic
- intro rail readiness reads for any proof with a music-only lead-in or voice-start offset, including `intro_rail_readiness_read`, `intro_active_title_read`, `intro_summary_legibility_read`, `intro_context_readability_read`, and `intro_transition_completion_read`
- rolling rail reads, including `rail_content_model_read`, `caption_display_model_read`, `caption_display_chunking_read`, `review_chrome_policy_read`, `highlight_render_policy_read`, `caption_window_role_read`, `caption_window_treatment_read`, `caption_highlight_source_read`, `caption_palette_source_read`, `old_context_rows_absence_read`, `minimal_anchor_read`, `rolling_caption_behavior_read`, `rolling_caption_state_hook_read`, `caption_scroll_smoothness_read`, `caption_window_fade_mask_read`, `caption_window_transparency_read`, `caption_key_phrase_span_read`, `caption_highlight_fade_read`, `caption_end_screen_rollout_read`, `end_screen_palette_contract_read`, `end_screen_target_fill_palette_read`, `end_screen_target_contrast_read`, and `no_cross_episode_default_palette_read`
- rail opacity/source visibility reads, including `rail_backlight_scope_read`, `right_rail_opacity_balance_read`, `context_region_source_visibility_read`, `caption_softener_scope_read`, and `caption_window_treatment_read`, to prove readability treatment stays localized around active text and captions without creating an opaque lower rail column
- chapter source-art motion reads, including `challenger_staged_transition_model_read`, `first_chapter_boundary_visual_ease_read`, `chapter_boundary_hard_shift_read`, `focused_transition_review_strip_read`, and `visual_state_debug_hook_read`, to prove source-art zoom, slide, drift, or lighting shifts follow the Challenger-staged transition model rather than hard-switching transform states

Human review checks pacing, glanceability, visual relevance, brand fit, audio-video timing, music contract fit, rolling caption placement/legibility/smoothness, key phrase highlight timing, `texture_noise_read`, readability treatment, ambient/effects layer reads, Challenger-staged chapter source-art motion, motion regression reads, `visible_cue_overlay_read`, end-screen caption rollout plus viewer-text suppression, and whether the episode feels authored.

Block rough assembly advancement if generated caption text does not normalize to the locked narration script, if ASR-derived words appear in generated captions, or if script/audio alignment coverage is below `98.5%` or has an unmatched script span longer than `8` tokens without a human-approved deviation ledger.

Block rough assembly advancement if rolling caption scroll is free-running instead of tied to audio/render time, if scrub/seek changes cause jumps or drift, if `window.__railCaptionStateAt(time)` or `window.__setRenderTime(time)` is missing, if highlighted phrases are not mapped to reviewed cue-map spans, or if caption-window blur/fill/background treatment appears without a human-approved readability override.

Block rough assembly advancement if the proof is voice-only, visual-only, missing music reads, missing full outro music, missing required caption/chapter retiming after a voice-start offset, missing a passing `vo_outro_music_blend_read`, or using the under-opening-voice bed plus short-tail regression when the contract says Challenger-style.

Block rough assembly advancement if a music-only intro or voice-start offset leaves the first minimal anchor or caption-ready rail state missing, ghosted, unreadable, or stuck in transition phase `0` before the first voice line.

Block rough assembly advancement if the right rail uses a broad full-height dark backlight or opaque lower column that hides the source image below the active scene text, unless a human-approved override explicitly scopes that look.

Block rough assembly advancement if the old previous/upcoming context rows remain visible under the first-eight rolling rail model.

Block rough assembly advancement if source-art zoom, slide, drift, or lighting states hard-switch at chapter boundaries instead of using the Challenger-staged transition model, unless a human-approved visual-system override explicitly scopes an abrupt cut or longer cinematic pre/post blend.

Block rough assembly advancement if a person-operated or subject-originated ambient effect has core origins on walkway sides, blank walls, plants, text panels, empty architecture, vehicle/equipment shells, or other excluded surfaces. Glow spill may reach nearby architecture, but the recorded origin point must remain on the approved subject-surface mask and must pass the episode-specific exclusion reads. For camera flashes/flashbulbs, broad line-band or strip sampling is also a blocker even when all generated points pass coordinate containment; the packet needs audited hotspots or pixel-tight masks plus zoomed proof artifacts. For vehicle/equipment practical lights, block advancement unless the packet includes a local origin map, per-origin visible-surface masks, exact core coordinates, explicit exclusions, and a zoomed calibration/contact-sheet proof, with reads equivalent to `vehicle_rear_origin_map_read`, `lamp_core_inside_rear_mask_read`, `no_free_floating_brake_lamp_read`, and `brake_lamp_alignment_overlay_absence_read`.

Block rough assembly advancement if any chapter title, context row, caption, cue label, diagnostic label, or other viewer-facing text remains visible or faintly visible behind the end-screen target geometry without a human-approved end-screen title policy, or if the rolling caption text/highlights have not faded fully to zero before the target window.

Block rough assembly advancement if `end_screen_palette_contract` is missing, stale against the approved backplate hash, fixed to Challenger/default colors without a named human-approved override, or lacks passing palette/contrast/default-reuse reads.

Block rough assembly advancement if any viewer-facing text appears outside the fixed right rail under `fixed_16x9_right_rail_v1`, or if ordinal-only labels appear as visible chapter/title copy, unless the packet carries a human-approved visual-system override naming the exact surface.

### 5. Final Assembly Gate

Review the final rendered video before upload.

Confirm:

- no placeholders or diagnostic artifacts remain
- no source-art, motion, thumbnail, or package surface has `texture_noise_read: tighten` or `texture_noise_read: reject`
- visible rail captions are burned into the final render and the approved VTT sidecar is preserved for YouTube upload, unless a human-approved caption waiver is recorded
- final visible rail captions normalize to the locked narration script, with ASR used only for timing
- caption timing follows the approved VTT cue timing without visible drift against the voice audio
- manual chapter timestamps are valid: first timestamp starts at `00:00`, at least three timestamps are present, timestamps ascend, chapters are at least 10 seconds long, and labels read as mini-hooks rather than generic section names
- title, thumbnail, and description match the episode promise
- title leads with the specific promise, not episode or show labeling; show branding comes after the promise
- thumbnail is a visual thesis with one tension and few words, not podcast art
- outro runs 15 to 30 seconds
- end-screen window is prepared for the final 5 to 20 seconds, holds static platform target geometry, records the background motion policy, and records `end_screen_hold_read`, `youtube_target_geometry_static_read`, `continuous_ambient_end_screen_preservation_read` when ambient motion continues, `end_screen_title_policy_read`, `final_luma_drop_read`, and `youtube_end_screen_safe_zone_read`
- final manifest carries the kept rough proof's passing `end_screen_palette_contract` or a refreshed passing contract against the same approved backplate; stale backplate hashes, copied Challenger/default colors, or missing contrast/default-reuse reads fail final assembly
- end-screen target geometry is free of faint residual chapter, context, caption, cue, or diagnostic text; record `end_screen_text_artifact_read` and `viewer_text_suppression_read`
- no fade-to-black, visible luma drop, or darkening occurs during the final platform overlay window
- final render manifest records `source_html_proof` path/hash, `current_kept_proof_render_source_read`, output path/hash, stream count, codec, duration, dimensions, fps, `full_decode_read`, caption sidecars, visible rail caption burn-in, downstream gate state, and any required `audio_source_encode_read`, `audio_stream_copy_read`, or `video_stream_copy_read`
- successor or variant finals pass `visual_freeze_read`, `proof_speedup_read`, and `post_change_regression_read`
- final mix conforms to the kept rough proof's `music_integration_contract`, including voice offset, fade-tail, full outro, end-screen handoff, subtle-tail under-VO level, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_source_continuity_read`, and `music_contract_regression_read`
- final render was preflighted by a deterministic final-gate validator or equivalent script check, proving the active audio mix is not stale, all VO-to-outro and subtle-tail reads pass, the transition sample exists, the full outro starts before voice end without restart, reaches target only after voice end, the end-screen template ID/geometry matches the approved Challenger/Therac default or a recorded human override, and the end-screen palette contract is present and passing
- audio levels and music mix are review-ready
- outro music is original, licensed, or cleared
- rights and Content ID notes are recorded

### 6. Publish Readiness Gate

Confirm:

- stable lifecycle `review.html` already exists for the episode; if final assembly is not kept yet, the page remains `lifecycle_stage: "in_progress"` and shows the current gate/blockers rather than claiming upload readiness
- primary review artifact is `review.html`, not a Markdown packet, and it renders the package with package-local relative media references
- HTML review page embeds the final MP4 with native controls backed by a byte-range-capable review server, attaches the approved upload VTT sidecar with a `<track>`, displays the thumbnail candidate, VO/music transition samples when relevant, key QA frames, and shows metadata, chapters, rights notes, end-screen choices, blocker state, and upload locks
- publish-readiness package copies or stages the final MP4, upload VTT/SRT, thumbnail candidate, QA frames, music/VO transition samples, metadata packet, and a range server script or equivalent local serving instruction into the package; record `publish_readiness_package_local_asset_copy_read`
- canonical human review URL is an HTTP localhost URL, not `file://`; record `publish_readiness_canonical_review_url`, `html_canonical_review_url_read`, `html_native_video_scrub_read`, and `html_range_server_read`
- publish-readiness manifest records `primary_review_artifact`, `review_surface_type`, `publish_readiness_review_html_path`, `publish_readiness_review_html_sha256`, `publish_readiness_canonical_review_url`, `html_primary_review_read`, `html_media_refs_read`, `html_native_video_scrub_read`, `html_range_server_read`, `html_canonical_review_url_read`, `publish_readiness_package_local_asset_copy_read`, and `html_upload_lock_read`
- cascadeeffects.tv remote review uses a stable `remote_review_url` at `/reviews/publish-readiness/{episodeId}`. Inception and in-progress manifests may omit `assets.video`; final publish-readiness refresh requires an unlisted YouTube receipt/status for the Cascade of Effects channel, `privacyStatus: unlisted`, `embeddable: true`, recorded processing status, `youtube_embed_permission_read`, `youtube_embedded_playback_ready_read`, and a no-large-video-upload read. The cascadeeffects.tv route remains unlisted/noindex; anyone with the YouTube watch URL or review URL may view the video once attached, so links stay limited to reviewers. If YouTube reports `embeddable: false`, repair the YouTube embed permission and republish the remote manifest before asking for remote-review keep.
- publish-readiness manifest carries the kept music contract reads, rights notes, exported VO/outro transition review sample, subtle-tail timing/gain fields, and any approved waiver record; missing or broad-only music evidence blocks publish readiness. A music-bearing episode must not pass publish readiness or upload prep unless `vo_outro_blend_plan_read`, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_transition_review_sample_read`, `outro_entry_level_match_read`, `outro_under_vo_masking_read`, `outro_target_after_voice_read`, `outro_prelap_source_read`, `outro_prelap_start_read`, `outro_no_restart_at_voice_end_read`, `outro_source_continuity_read`, and `music_contract_regression_read` are present and passing.
- publish-readiness manifest carries `rail_content_model_id: rolling_caption_anchor_v1`, `caption_display_model: rolling_rail_caption_window_v1`, `caption_display_chunking: script_locked_chunk_split_v1`, `review_chrome_policy: hidden_in_render_mode`, `highlight_render_policy: reviewed_cue_map_spans_only`, `rolling_caption_rough_keep_read`, and `caption_end_screen_rollout_read`; first-eight publish readiness and YouTube action stay blocked until the refreshed rough proof and final assembly based on this rail model are both kept.
- publish-readiness manifest carries a passing `end_screen_palette_contract` with the approved backplate path/hash, palette source, target fill/border/subscribe/text/accent values, contrast reads, and `no_cross_episode_default_palette_read`; inception and in-progress lifecycle manifests may carry a placeholder blocker before an approved backplate exists, but final publish readiness cannot.
- YouTube metadata, description, chapters, thumbnail, playlist, and optional podcast placement
- title, description, chapters, hashtags, and tags have been drafted or QA'd through `youtube_metadata_copywriting_v1`; record `youtube_metadata_copywriting_read`
- public YouTube title, description, chapter labels, tags, and thumbnail text are audience-facing copy, not implementation notes. Record `public_metadata_copy_read`; block publish readiness if public copy contains workflow terms such as `long-form episode`, `publish-readiness`, `proof`, `render`, `sidecar`, `package`, `review surface`, `upload candidate`, or other internal production language, except inside clearly separated diagnostics.
- public YouTube tags must be viewer-facing search intents or episode-central entities. Record `public_tag_relevance_read`; remove research-source, scholar, author, or incidental person-name tags unless the name is part of the public title/description positioning or has an explicit human-approved discoverability reason.
- end screen target, subscribe path, next-video path, or playlist path
- Related Video links from existing Shorts where available
- Related Video links for new or revised Shorts are planned when a Shorts expansion is scoped
- Day 1-7 and Day 8-14 Shorts waves are noted when a full Shorts expansion is scoped
- caption package: rendered rail captions plus approved VTT sidecar path/hash, locked script text source path/hash, timing source path/hash, script/text match read, alignment coverage read, ASR-text-not-used read, or a human-approved waiver with affected outputs named
- final-render package: source HTML proof path/hash, output MP4 path/hash, audio encode/copy policy, full decode, duration, H.264/AAC stream reads, `1920x1080`, `24fps`, caption sidecar read, visible rail caption burn-in read, and downstream gate read
- rights, source, and Content ID risk
- visibility recommendation

Human approval is required before unlisted YouTube review upload, public release, scheduled release, or visibility changes. An unlisted YouTube upload created for cascadeeffects.tv review is review-only and does not authorize public/scheduled visibility.

### 7. Post-Publish Learning Gate

Record:

- title and thumbnail performance signal
- chapter retention notes
- Short bridge performance
- comments or audience questions worth carrying forward
- next episode packaging implications
- whether the MVP template should stay, tighten, or expand

## MVP Template

For the first 3 to 5 long-form videos, keep the format constrained:

- custom thumbnail
- voice-led episode
- reviewed Living Cover ambient/effects layer, including an explicit `none|minimal` lane when restraint is the right choice
- reviewed music integration contract using the Challenger-style series precedent unless a human-approved alternate or waiver is recorded
- right-rail chapter/title cadence under `fixed_16x9_right_rail_v1`
- key phrase typography every 1 to 2 minutes inside the rail or as non-textual source-safe behavior
- 4 to 6 cascade diagrams or effect-map moments expressed as rail behavior or non-textual source-safe motion unless an override scopes another surface
- existing brand illustrations where relevant
- dual captioning: visible rail captions plus approved VTT sidecar
- manual chapters
- 15 to 30 second outro song
- end screen with next video, playlist, or subscribe path
- one related Short where available

## Output Packet

Return this packet for every run:

```yaml
stage:
phase_gate:
episode_id:
long_form_audio:
frontier_model_script_critique:
critique_integration:
human_script_approval_for_audio:
script_audio_source_integrity:
existing_short_bridge:
short_candidate_map:
shorts_wave_note:
brand_contracts_checked:
brand_assets:
review_artifacts:
variant_integrity_context:
render_integrity_context:
end_screen_context:
ambient_effects_context:
music_integration_contract:
final_render_contract:
readability_context:
captioning_process_version:
caption_required:
caption_output_model:
caption_source:
caption_qa:
caption_waiver:
youtube_packaging:
publish_readiness_review:
rights_review_required:
human_review_required: true
may_advance: false
disposition: draft | review_ready | keep | tighten | reject | defer | blocked
blockers:
next_action:
```

Only a clear human approval may set `disposition: keep` for a phase. Even then, keep `may_advance: false` unless the current task explicitly asks to prepare the next phase.

## Operating Rules

- If asked to start long-form video production, begin at the Inventory Gate unless an inventory already exists and is human-approved.
- If asked to render, generate, refresh, promote, or keep long-form voice audio, first confirm frontier-model script critique, critique integration, and explicit human script approval for audio are passing for the exact script revision. If any are missing, do not render audio; create or update a blocker/backfill packet instead.
- If existing long-form audio was already rendered without the script gate, mark it diagnostic/review-only and block downstream advancement until the critique, integration, and human approval records are backfilled or a human waiver is recorded.
- If asked to build visuals, confirm the Episode Package Gate and Visual System Gate are `keep` first.
- If asked to bootstrap or incept an episode, create the stable local lifecycle review packet and publish its placeholder manifest to cascadeeffects.tv unless `--skip-remote-review` is explicitly used. Missing Vercel Blob credentials should leave the local packet in place and fail loudly.
- If asked to build a Living Cover rough proof, confirm the cue map, ambient/effects layer, and music integration contract artifacts exist; missing cue/ambient artifacts block motion readiness and rough assembly, and a missing music contract or waiver sets `review_ready_blocked_missing_music_contract`.
- If asked to mark a Living Cover rough proof `keep`, confirm the music contract reads are passing or an explicit human waiver is present, and confirm `end_screen_palette_contract` is present and passing once an approved backplate exists. Do not accept `keep` for a voice-only, visual-only, temp-music, missing-palette, stale-palette, or copied-default-palette proof unless the waiver/override names the affected output and next action.
- If asked to render a final, confirm Rough Assembly Gate is `keep` first and render from the current kept HTML proof path/hash.
- If the human marks final assembly `keep`, record the final assembly keep and create or update the HTML-first publish-readiness package next. Keep upload, publish, schedule, and visibility flags false.
- If artifact-safety reads or historical/source-reference accuracy reads are `tighten` or `reject`, block promotion even when the visual direction is otherwise approved.
- If asked to upload or publish, return an HTML-first Publish Readiness Gate package first. Do not perform upload, publish, schedule, or visibility changes until the HTML review package exists, is served through a byte-range localhost URL, carries passing VO/outro blend and subtle-tail evidence or an explicit waiver, the package is kept, and explicit human approval for that action is recorded.
- If auditing older unreleased long-form videos, treat any final or publish-readiness package without the VO/outro blend sample and actual-outro prelap reads as `tighten_missing_vo_outro_blend_gate`, even if it has broad music, level, or full-outro reads.
- If asked for long-form editorial strategy, route to the series bible skill.
- If asked for long-form audio-only script production, route to the long-form script/audio production path.
- If asked for a new or revised Short, route to the active Shorts production skill.

## Edge Cases

- If the brand contracts are missing or unreadable, block the Visual System Gate and name the missing path.
- If Claude is unavailable, use another human-approved frontier model for script critique and record the substitution rationale.
- If a script is marked `locked` but lacks frontier-model critique, critique integration, or human approval for audio, block long-form audio render and treat any already-rendered audio as diagnostic-only.
- If existing audio is stale, missing, or mismatched to the episode package, block and route to audio/script refresh.
- If an episode has no approved music contract yet, use the Challenger-style default as the planning baseline. Hyatt, Tacoma, and other future long-form episodes must remain blocked at rough-proof keep/final/publish gates or carry an explicit human-approved alternate/waiver until their music contract exists.
- If an existing Short has unresolved rights, final-export, or publish-review blockers, list it as a bridge candidate but do not treat it as publish-ready.
- If the episode needs a visual style outside the brand contracts, require explicit human approval before rough assembly.
- If YouTube chapter, end-screen, or Related Video requirements may have changed, recheck current YouTube guidance before publish readiness.
