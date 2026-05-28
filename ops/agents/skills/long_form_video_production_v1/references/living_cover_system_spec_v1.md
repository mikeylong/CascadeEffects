# Living Cover System Spec v1

This spec codifies the reusable long-form Living Cover system for Cascade Effects episodes. It is a production default for the 186-episode long-form slate, with explicit human-reviewed override paths for episode-specific subject, safe-space, or story needs.

The Challenger full-runtime fixed 16:9 larger native rail captions proof is the reference implementation for this preset. It is not a global visual carrier and does not make the Challenger proof a `keep`.

## System Identity

- `living_cover_system_version`: `living_cover_system_v1`
- `rail_preset_id`: `fixed_16x9_right_rail_v1`
- `captioning_process_version`: `living_cover_captioning_process_v1`
- `ambient_effects_process_version`: `living_cover_ambient_effects_layer_v1`
- `override_status`: `none | proposed | approved`
- Default role: long-form YouTube Living Cover review proof and eventual video carrier.
- Scope: long-form video production only. This spec does not govern Shorts, podcast feeds, homepage cards, thumbnails, or publish actions unless another reviewed plan imports it.

## Canvas And Review Shell

- The video canvas is fixed `1920x1080` / `16:9`.
- The browser is only a review shell. It may uniformly scale the fixed canvas to fit the viewport and letterbox or pillarbox outside the frame.
- The canvas contents must not reflow with viewport size. Rail width, rail position, typography, copy hierarchy, source-art composition, and safe-space geometry stay in fixed design coordinates.
- Audio controls stay outside the render canvas and hide in render mode.

## Visual Carrier

- Each episode uses an approved episode-specific raster/source-art carrier.
- ImageGen-generated `1920x1080` raster source art is the default and primary production source for long-form Living Cover imagery. Use the Codex `imagegen` skill with built-in `image_gen` unless a human-approved plan explicitly chooses another generator.
- Sourced archival stills, sourced video frames, and deterministic local compositions are reference evidence by default. They may guide ImageGen prompts, historical/source-reference review, contact sheets, and QA, but they are not the default production backplate.
- A sourced raster/source-art, hybrid sourced carrier, or deterministic composition over source media can become active source art only with a packet-local human-approved exception that records the episode, reason, exact source paths/hashes, rights/source-risk read, affected outputs, and why ImageGen is insufficient for that gate. Otherwise the carrier is `reference_only` or `diagnostic_only`.
- HTML, CSS, SVG, canvas, and JavaScript may only provide the proof shell, timing, captions references, rail, deterministic typography, safe-zone layout, masks, transforms, and layer compositing over approved visual assets.
- Local Python, HTML, CSS, SVG, canvas, FFmpeg, or Playwright output may not be promoted as a generated source-art backplate; local tools may only package, resize, preview, mask, QA, and assemble approved raster assets into the proof shell.
- Generated source-art backplates must be judged against episode-specific historical/source-reference accuracy before promotion. The review must define the real-world anchor facts the image is claiming to show, cite or list the reference basis used to judge them, and record `historical_accuracy_read`, `source_reference_alignment_read`, `public_anchor_geometry_read`, and any episode-specific read such as `hyatt_atrium_architecture_read`. A strong-looking image with the wrong architecture, equipment, public anchor, period setting, or source relationship is not a keeper.
- Do not treat CSS/SVG/canvas-drawn public anchors, evidence objects, or living-cover backgrounds as advancement sources unless a later human-approved plan explicitly scopes them as production assets.
- Long-form Living Cover episode backplates default to `cascade-ink-lit-photoreal-v1` or an episode-specific source-preserving/photoreal public-scene carrier. This is the default "ink-lit" long-form lane.
- `cascade-paper-architectures-ink-lit-v1` is allowed only for CascadeEffects.tv website assets, YouTube channel-level branded visual assets, and CascadeEffects.tv website thumbnail-gallery images. It is never an active long-form video asset lane.
- Long-form source-art prompts, visual-system plans, source-art manifests, rough proofs, finals, cover frames, in-video end screens, and thumbnail candidates must record `video_visual_style_scope_read` and `paper_architecture_visual_style_read` before advancement. Folded-paper/foam-core aircraft or building models, paper planes, paper cutaway tableaux, cream paper forms, clean paper planes, and other Paper Architecture resemblance cues are `reject`.
- Challenger's photoreal ink-lit launch-pad carrier is the reference proof for the photoreal/source-preserving lane, not a global scene template.
- Public-scene, institutional, human/tableau, crowd, or event-based source-art carriers should include anonymous human presence unless a visual-system plan records a human-presence waiver. Keep people at a distance, turned away, in silhouette, partially occluded, motion-softened, or otherwise non-identifiable. Do not use face-forward close-ups, identifiable likenesses, celebrities, public officials, victim portraits, or generated faces that could read as a real person. Record `human_presence_read` and `no_recognizable_faces_read`; missing required human context is a `tighten` blocker, and a recognizable face is a `reject` blocker.
- Source-art compositions should create implied action, anticipation, and ambient/effects affordance. Avoid foreground clipboards, binders, folders, paperwork stacks, legal pads, and generic desk evidence as the dominant visual anchor; they are low-energy administrative props and usually block a Living Cover from feeling alive. Such props are allowed only with a human-approved episode exception that names the exact object, explains why it is mechanism-critical, keeps it from dominating the foreground, and records `foreground_admin_prop_exception_read: pass`. Record `foreground_admin_prop_read`, `implied_action_anticipation_read`, and `ambient_affordance_read` before source-art `keep`.
- Photoreal/source-preserving proofs must not include procedural cyan signal lines, diagnostic traces, connector lines, generated UI paths, or canvas/SVG overlay marks on top of the source-art backplate unless the visual-system plan explicitly approves the overlay. Record `procedural_signal_overlay_read` and `ambient_line_artifact_read`; visible stray line overlays are a `tighten`/`reject` blocker.
- Rail panel and backlight colors are episode-local. Choose the active-panel fill, end-screen target fill, muted rail text, and small accent colors from the approved source-art palette or a clearly harmonized darkening of that palette. Challenger's navy panel is acceptable only when it is scene-matched to a night-sky/launch-pad backlight; it is not the default Living Cover rail color. Record `end_screen_palette_contract`, `rail_panel_palette_read`, `source_integrated_panel_color_read`, and `no_cross_episode_default_palette_read`. If a proof uses a fixed cross-episode rail or target color that does not visually belong to the backplate, block advancement as `tighten` or `reject` unless a human-approved override names the reason and affected outputs.
- `end_screen_palette_contract` is required once an approved backplate exists. It must record the approved backplate path/hash, `palette_source: sampled_episode_backplate` or `human_approved_override`, sampled/harmonized colors for `video_target_fill_rgba`, `video_target_border_rgba`, `video_target_secondary_border_rgba`, `subscribe_ring_rgba`, `muted_rail_text_hex`, and `small_accent_hex`, contrast/readability reads, and `no_cross_episode_default_palette_read`.
- Avoid broad full-frame dark translucent overlays over approved source-art backgrounds. If readability needs help, use localized soft treatment behind the active panel, title, or caption regions and record the treatment in the proof manifest.
- Avoid full-height opaque right-column treatments below the active scene text. The active panel may have a panel fill, and captions may have a localized lower-rail softener while captions are visible, but the chapter context/list region should leave the source image visible. Record `rail_backlight_scope_read`, `right_rail_opacity_balance_read`, `context_region_source_visibility_read`, and `caption_softener_scope_read`.
- Paper Architecture website, channel-brand, and website thumbnail-gallery surfaces must preserve the illustration contract's minimal paper texture rule: clean paper, subtle fiber only, and no stone/grit/noisy material read. Photoreal/source-preserving long-form episode backplates instead use subject-specific realism, hygiene, human-role, text/logo, Paper Architecture rejection, and safe-space reads.

## Generation Provenance

Every generated raster, generated motion carrier, or deterministic rendered carrier must record explicit `generation_provenance`.

- Required fields: `tool`, `model`, `model_confidence`, `mode`, source-generation path/hash, final packet asset path/hash, prompt path/hash when applicable, init/reference image path/hash when applicable, and `provenance_notes`.
- Allowed `tool` values include `codex_builtin_image_gen`, `mflux_generate_z_image_turbo`, `apple_ltx23_ltx_2_mlx`, `comfyui_flux`, and `deterministic_composition`.
- Use `model_confidence: explicit` when the manifest or runtime command names the model. Use `model_confidence: inferred_from_path` when the tool family is inferred from paths such as `/Users/mike/.codex/generated_images/.../ig_*.png`. Use `model_confidence: unknown` only when neither the model nor a reliable tool-family clue is available.
- Built-in Codex image-generation assets under `/Users/mike/.codex/generated_images/.../ig_*.png` should record `tool: codex_builtin_image_gen`, `model: unknown_builtin_image_gen_model`, and `model_confidence: inferred_from_path` unless a future manifest records the exact backend model.
- Deterministic HTML, Python, FFmpeg, or Playwright assembly is not generative source art, but final and proof manifests should still record it as `tool: deterministic_composition` when it creates a review carrier from approved assets.
- Generated source-art manifests must also record `imagegen_skill_read`, `source_art_generation_tool_read`, `local_rendered_backplate_read`, and `source_art_workspace_copy_read` when the asset is produced through built-in ImageGen and copied into an episode packet.
- Non-ImageGen source-art exceptions must record `source_art_generation_tool_read: pass_human_approved_non_imagegen_exception`, `imagegen_primary_source_exception_read`, and the source/rights reads named in the exception.

## Historical Accuracy Review

Generated and sourced Living Cover carriers must pass a historical/source-reference review before they can be selected for motion readiness.

- Define `historical_accuracy_context` with the episode's real-world visual target, canonical visual facts, allowed abstractions, and hard mismatch blockers.
- Record the reference basis as local paths or public source URLs. For source-preserving or photoreal public-scene work, include the active source frames or research references used to judge the output.
- Required reads: `historical_accuracy_read`, `source_reference_alignment_read`, `public_anchor_geometry_read`, `video_visual_style_scope_read`, `paper_architecture_visual_style_read`, and at least one episode-specific read for the central architecture, equipment, vehicle, room, or public-scene anchor.
- For Hyatt Regency atrium source art, the episode-specific read is `hyatt_atrium_architecture_read`; it must judge multi-story atrium identity, suspended walkway placement, visible hanger rods, box-beam/load-path plausibility, balcony/room openings, and public-event floor relationship.
- `pass` means the generated image preserves the episode-central visual facts with only acceptable abstraction. `tighten` means it is useful but needs architectural/equipment/period repair before selection. `reject` means it contradicts the historical/public anchor or could mislead the viewer.

## Right Rail Preset

Use the rail only in fixed `1920x1080` design coordinates:

- Rail side: right.
- Rail width: `760px`.
- Right margin: `52px`.
- Left edge: `1108px`.
- Top and bottom inset: `52px`.
- Active panel radius: `8px` maximum.
- Active panel padding: `34px 36px 36px`.
- Rail gap below active panel: `28px`.
- Context row gap: `15px`.
- Dot size: `8px`; dot column `24px`; row text gap `16px`.
- Legacy caption slot preset: `native_rail_caption_slot_v1`.
- Current first-eight rail content model: `rolling_caption_anchor_v1`.
- Current first-eight caption display model: `rolling_rail_caption_window_v1`.
- Current rolling caption chunking model: `script_locked_chunk_split_v1`.
- Current review chrome policy: `hidden_in_render_mode`.
- Current highlight render policy: `reviewed_cue_map_spans_only`.
- Caption window role: `middle_two_thirds_right_rail`.
- Caption window treatment model: `transparent_caption_mask_only_v1`.
- Caption blur scope: `none`.
- Caption highlight source: `living_cover_cue_map_key_phrases`.
- Caption palette source: `sampled_episode_backplate`.
- Caption window placement: middle two-thirds of the fixed right rail safe area, with no card, badge, border, glow, new accent color, progress bar, timecode, karaoke effect, or out-of-rail text.
- No left accent rules, repeated card borders, visible evidence rows, global vignette, full-frame gradients, baked progress bars, or top timecode.
- Viewer-facing text boundary: all story text, chapter text, captions, cue/effect-map wording, and end-screen wording must stay inside the fixed right rail unless an approved override names the exact out-of-rail surface. Left-side chapter slates, effect cards, lower thirds, standalone cue cards, bottom-left end labels, and diagnostic text panels are blocked by default.

## Rail Backlight And Source Visibility

The rail is a text-placement preset, not a license to cover the right third of the image with a full-height dark pane.

- Active scene text may sit inside the active panel, with a source-aware fill and localized shadow.
- Legacy context rows should remain legible through text color, shadow, and modest localized support, not through a continuous opaque column behind the whole rail.
- For `rolling_caption_anchor_v1`, prior/upcoming context rows are removed. The top rail anchor may be suppressed for caption-only reviews; when present, it must stay minimal. The middle/right caption window carries the narrated text.
- Rolling caption readability defaults to transparent caption-window treatment: no blur, fill, translucent panel, or background effect behind the caption container. Use text color, text shadow, and the caption entry/exit mask before considering any human-approved readability override.
- Source art below and around the active scene text must remain visibly present at representative chapter samples.
- Required reads: `rail_backlight_scope_read`, `right_rail_opacity_balance_read`, `context_region_source_visibility_read`, `caption_softener_scope_read`, `caption_window_treatment_read`, `full_frame_dark_overlay_read`, and `localized_readability_treatment_read`.
- A broad full-height dark backlight, opaque lower rail column, or context-region veil that hides the source image is a `tighten` blocker unless a human-approved visual-system override scopes it for that episode.

## Typography Preset

Use real fixed-canvas font sizes. Do not use transform scaling on rail, panel, label, title, summary, or context text.

- Typeface: Inter or the local system fallback already used by the proof shell.
- Active chapter label: `26px`, uppercase, `830` weight, line-height `1`, letter spacing `0.04em`, strong secondary contrast.
- Active beat title: `64px`, `820` weight, line-height `0.94`, letter spacing `0`.
- Chapter summary: `34px`, `650` weight, line-height `1.12`, high contrast.
- Context title rows: `28px`, `720` weight, line-height `1.04`, muted secondary contrast.
- Rolling rail captions: target `32-34px`, `590` weight, line-height around `1.16-1.18`, stable fixed metrics, rail cream/source-sampled secondary color treatment, and generous spacing proportional to the rail. Long cues must split into 1-2 readable-line chunks before layout.
- No critical rail text may be treated as small interactive-web text. The rail must remain legible after YouTube compression and at preview scale.

## Content Model

- Use `6-8` major sections for a full episode unless the Episode Package Gate approves a different chapter count.
- Under `rolling_caption_anchor_v1`, the active rail either suppresses the top anchor or shows only a minimal chapter/beat anchor. Do not render large title/chapter copy above the rolling captions.
- The old prior/upcoming context list is removed for first-eight long-form rough proofs using this model.
- Legacy active panel/context-list proofs may not advance to final assembly, publish readiness, or upload gates for first-eight episodes until a successor rolling-caption rough proof receives human `keep`.
- Do not show generic labels such as `Decision Chain`, `Current Scene`, `Build-Up`, `Previous`, `Current`, `Upcoming`, or count labels such as `5 upcoming`.
- Do not show ordinal-only labels such as `CHAPTER 01`, `PART 1`, or `SECTION 03` as viewer-facing rail copy. If numbering is needed, keep it internal or pair it with semantic episode-specific text under an approved policy.
- Keep copy sparse enough to read as video, not as an interactive web app.
- Right-rail labels must be episode-specific viewer-facing language. Active rail data must be checked for stale cross-episode labels and internal production labels; record `stale_cross_episode_label_read` before rough proof, final assembly, or publish readiness can advance.
- Rough proofs must inventory visible text-bearing elements and record `viewer_text_surface_inventory_read`, `right_rail_text_boundary_read`, `out_of_rail_text_read`, and `ordinal_chapter_label_read` before they can advance.

## Living Cover Cue Map

Every Living Cover rough proof needs a packet-local `living_cover_cue_map` artifact before rough assembly. The cue map turns the chapter spine into authored video behavior: chapter shifts, key phrase typography, 4 to 6 effect-map or cascade-diagram moments, source-safe motion/composition changes, caption/rail coordination, and outro/end-screen cue timing.

- The cue map is separate from the chapter map. A chapter map names where the episode is; the cue map names what the Living Cover does there.
- The cue map is an internal production artifact. Do not render it as a standalone viewer-facing card, panel, node list, label, status readout, or text surface. In particular, proof frames must not show labels such as `Living Cover Cue`, `Outro Cue`, `cue map`, cue IDs, treatment names, QA reads, or implementation status unless a human-approved visual-system plan explicitly scopes a visible diagnostic review surface.
- Cue treatments must stay inside the approved carrier policy. For photoreal/source-preserving backplates, cues may use right-rail transitions, right-rail typography, non-textual effect-map behavior, localized rail readability treatments, opacity, transform, or accent strength; they must not add out-of-rail text panels, diagnostic connector lines, cyan signal traces, generated UI paths, or other procedural marks over source art unless a human-approved visual-system plan explicitly scopes them.
- Each cue should reference a script/chapter anchor, a time range, a treatment type, the layer it affects, and the QA read that proves it is source-safe and legible.
- Rough-proof manifests must record `living_cover_cue_map_read`, `chapter_cue_coverage_read`, `typography_cue_read`, `effect_map_cue_read`, `source_safe_motion_read`, `cue_no_diagnostic_overlay_read`, `cue_map_internal_artifact_read`, and `visible_cue_overlay_read`.

## Ambient/Effects Layer

Every Living Cover rough proof needs a packet-local `living_cover_ambient_effects_layer` artifact before motion readiness and rough assembly. The ambient/effects layer is separate from the cue map and the music integration contract: the cue map defines story and typographic behavior, the ambient/effects layer defines source-integrated motion, micro-life, occlusion, and QA, and the music integration contract defines soundtrack timing, retiming, mix, and rights gates.

- The artifact must declare one or more lanes: `none`, `minimal`, source drift/lighting, particles or dust, practical lights or screen glow, public-scene motion such as aircraft or vehicles, or a mixed episode-specific lane.
- `none` or `minimal` is a valid lane only when the artifact records a rationale, the episode's visual restraint reason, and passing review reads. A missing ambient/effects artifact blocks motion readiness, rough assembly, final render, and publish readiness.
- Effects must preserve the approved source-art carrier. Procedural motion may composite over approved raster/source art, but it must not become a new source-art backplate or add diagnostic marks over photoreal/source-preserving imagery.
- When an effect needs depth, the source plate, matte, and effect canvas must share the same fixed `1920x1080` coordinate space. Record source-plate/matte registration and foreground occlusion reads before using particles, aircraft/vehicles, screen glow, or other effects that interact with scene depth.
- Effects are additive by default. Successor proofs that add a new effect must preserve prior approved layers unless the review packet explicitly scopes a replacement.
- Deterministic effects must record seed, count, speed, route, anchor, opacity, and timing parameters needed to reproduce the proof.
- When an event-life effect represents ongoing public activity and the review intent is "active from the start," the schedule may be prewarmed. Prewarming must be explicit in the ambient manifest: record original timing, negative `start_seconds` or equivalent initial progress, preserved source origins, count preservation, and opening-frame proof. A prewarm is a timing technique over approved effects, not permission to add new people, objects, source-art edits, or viewer-facing debug marks.
- Full-frame flash pulses may be used only as secondary exposure reactions to validated source-locked flash events. They must not replace the visible person/equipment flash core, must not be sourced from broad regions, and must carry a subtlety cap, defaulting to `0.075` alpha or lower unless a human-approved episode override records masking evidence. Record pulse source, max alpha, aggregate cap, end-screen cap, `fullscreen_flash_pulse_read`, `flash_pulse_subtlety_read`, `flash_core_origin_preservation_read`, and origin-preservation reads.
- Camera flashes and flashbulbs default to `period_xenon_pop_with_video_bloom_v1`: the manifest records a very short physical flash reference, a fast attack, a one-frame peak hold, a short 24fps-visible bloom, a compact cream-white core, a bounded warm halo, and no lingering dot after the documented decay window. Long half-second glow treatments are stylized overrides and require `human_approved_stylized_long_flash_override_read`.
- A full-frame flash pulse also requires local-source visibility. The subject/equipment core must read at video-review scale at peak, the halo must stay bounded so nearby architecture can catch spill without becoming the origin, and QA must sample event start, peak, +1/+2/+4 frames, and post-decay. Record `period_camera_flash_behavior_read`, `xenon_pop_duration_read`, `video_bloom_decay_read`, `flash_core_peak_visibility_read`, `global_pulse_peak_coupling_read`, `flash_halo_boundary_read`, `no_lingering_flash_dot_read`, `per_hotspot_recycle_spacing_read`, and `flash_not_strobe_read`.
- Browser QA must sample representative times for start, middle, chapter-transition, and outro/end-screen behavior. Long proofs must also use a byte-range-capable review server or equivalent range-scrub path so late-episode effects can be checked without replaying from the start.
- Debug overlays, matte previews, route overlays, QA labels, implementation-status panels, and effect-lane names are review artifacts only. They must not render into the viewer-facing proof unless an explicit human-approved diagnostic surface is scoped.
- Required reads: `ambient_effects_plan_read`, `ambient_effect_lane_decision_read`, `source_plate_matte_registration_read`, `foreground_occlusion_read`, `effect_layer_source_safety_read`, `deterministic_ambient_read`, `additive_effect_integration_read`, `debug_overlay_absence_read`, `ambient_effect_browser_sample_read`, and `range_scrub_effect_review_read`.
- Optional per-effect reads include `localized_particle_density_read`, `particle_foreground_leak_read`, `public_motion_occlusion_reappearance_read`, `practical_light_micro_life_read`, and `screen_glow_motion_read`. Use `not_applicable` when the lane is not selected.

## Music Integration Contract

Every Living Cover rough proof needs a packet-local `music_integration_contract` artifact before rough assembly and before rough-proof `keep`. This contract is separate from the ambient/effects layer and from final audio mastering. Its job is to make the soundtrack decision explicit early enough that timing, captions, chapters, end-screen pacing, and review feel cannot drift.

- Valid lanes are `challenger_style_intro_outro`, `episode_alternate_contract`, or `no_music_or_temp_music_waiver`.
- Challenger is the default series precedent unless a human-approved alternate or waiver names the episode and affected output. The default pattern is approved intro music, a music-only lead-in when the intro source has one, a recorded `voice_start_offset_seconds`, a 2-second intro fade tail under VO when using the Challenger pattern, full outro music through the end-screen window, `subtle_tail_outro_v1`, and a deterministic `storyTimeAt(audioTime)` or equivalent model so chapters, captions, cue maps, and rail behavior follow story time after the voice offset.
- `subtle_tail_outro_v1` requires the approved full outro source to enter only under the last 1-2 seconds of VO at a low bed level, stay clearly below the final spoken phrase, reach target level only after voice end, continue without restart, and carry the static end-screen window. Bridges, motif loops, or proxy sources may only supplement the mix; they cannot be the only music under the last VO phrase before the real outro starts.
- Broad actual-outro prelap models are opt-in exceptions, not Challenger defaults. A full-outro prelap longer than 2 seconds, an under-VO gain above the subtle-tail bed, or an outro target level reached at voice end must carry `human_approved_prelap_override` with the episode/output, rationale, exact timing/gain values, and masking evidence; otherwise final-gate and publish-readiness validation must fail it even if generic blend reads say `pass`.
- The contract must record approved intro/outro source paths, hashes, source rights, Content ID risk, duration/stream reads, level targets, fade/ramp curves, voice-start offset, end-screen window, final-VO-to-outro fade or ramp approach, level-match and masking notes, a short transition review sample around the final VO line into the first outro seconds, and browser sample times at intro, voice boundary, fade end, chapter anchors, outro start, end-screen hold, and final second. For the default Challenger lane, it must also record `full_outro_source_path`, `full_outro_start_seconds`, `voice_end_seconds`, `outro_prelap_seconds`, `outro_under_vo_gain_linear`, `outro_target_gain_linear`, `outro_reaches_target_at_seconds`, `under_vo_music_margin_db`, and `outro_no_restart_at_voice_end`.
- Final render preflight must validate this contract deterministically. A render must fail if the active audio mix has no `vo_outro_blend_plan`, no exported transition sample, stale manifest paths, or non-passing `vo_outro_blend_plan_read`, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_transition_review_sample_read`, `outro_entry_level_match_read`, `outro_under_vo_masking_read`, `outro_target_after_voice_read`, `outro_prelap_source_read`, `outro_prelap_start_read`, `outro_no_restart_at_voice_end_read`, `outro_source_continuity_read`, or `music_contract_regression_read`.
- When the voice start is offset, captions and transcript sidecars must be regenerated or retimed from the locked-script caption text. Record `caption_timing_shift_read` and keep ASR text as timing-only.
- When the voice start is offset, the first right-rail state must be fully readable throughout the music-only lead-in unless a human-approved cold-open override names another treatment. Implementations must not let `storyTimeAt(audioTime)` clamping at `0` hold the first chapter at transition phase `0`; active title, summary, active panel, and relevant context rows must render at settled opacity at `t=0`, mid-intro, and `voice_start_offset_seconds`.
- The end-screen music handoff must carry full outro music through the static YouTube target-geometry window unless a human-approved alternate records the reason.
- The final VO-to-outro transition must feel like an intentional continuation of the last spoken moment, not a hard join, level jump, clipped tail, dead-air gap, unrelated music slam, post-VO music start, or music bed that crowds the last words. Programmatic level checks are supporting evidence only; `vo_outro_music_blend_read` and `vo_outro_perceptual_review_read` require a perceptual listen-review pass on the exported transition sample, `outro_under_vo_masking_read` requires stem-level evidence that music stays below the final phrase, and `outro_source_continuity_read` requires proof that the full outro source is already present before the final word and does not restart at voice end.
- Therac/Challenger regression rule: do not use an under-opening-voice bed plus a short 15-second tail when the request or series precedent says to match Challenger. Use music-only intro, voice offset, fade tail, and full outro; record `music_contract_regression_read`.
- A no-music or temp-music path is an exception. `no_music_or_temp_music_waiver_read` may pass only with human rationale, affected episode/output, affected downstream gates, and the next required music action. Without that waiver, missing music sets `review_ready_blocked_missing_music_contract` and blocks rough-proof `keep`, final render, final assembly, publish readiness, upload prep, and release.
- Required reads: `music_integration_plan_read`, `series_music_contract_read`, `approved_music_source_read`, `intro_music_contract_read`, `voice_start_offset_read`, `caption_timing_shift_read`, `full_outro_music_read`, `end_screen_music_handoff_read`, `vo_outro_blend_plan_read`, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_transition_review_sample_read`, `outro_entry_level_match_read`, `outro_under_vo_masking_read`, `outro_target_after_voice_read`, `outro_prelap_source_read`, `outro_prelap_start_read`, `outro_no_restart_at_voice_end_read`, `outro_source_continuity_read`, `audio_level_mix_read`, `music_rights_read`, and `music_contract_regression_read`.
- Exception read: `no_music_or_temp_music_waiver_read`. It should normally be `not_applicable_no_waiver_requested`; it only passes when the explicit waiver record exists.

## Music-Only Intro Rail Readiness

For `challenger_style_intro_outro` and any other contract with a voice-start offset, the first visible rail state is part of the intro, not a delayed animation that waits for narration time to advance.

- Sample the proof at `t=0`, mid-intro, and `voice_start_offset_seconds`.
- The first active chapter label, active title, active summary, active panel, and context rows must be visible and readable in those samples.
- Implementations may use audio time, an explicit intro state, or a first-section exception to settle the rail before narration begins. They must not base first-section intro opacity only on `storyTimeAt(audioTime) - section.at` when story time is clamped at `0`.
- Context rows should remain secondary but legible; a proof with ghosted or unreadable context rows during the intro is a `tighten`.
- Captions remain suppressed before voice start unless an explicit cold-open caption override is approved.
- Required reads: `intro_rail_readiness_read`, `intro_active_title_read`, `intro_summary_legibility_read`, `intro_context_readability_read`, and `intro_transition_completion_read`.

## Captioning Process

Use `living_cover_captioning_process_v1` for every long-form Living Cover episode.

- Captions are required by default: `caption_required: true`.
- Default output model: `caption_output_model: dual_visible_rail_and_youtube_vtt_sidecar`.
- The locked narration script is the only source of visible caption text.
- ASR, WhisperX, VTT, and SRT artifacts are timing sources only. Never copy generated ASR words into visible rail captions or YouTube sidecars.
- Build captions with `scripts/build_living_cover_script_locked_captions.py` or an equivalent deterministic script-locked builder.
- Strip nonspoken performance tags such as `[calm]` or `[deliberate]` from script text before caption generation.
- Preserve script punctuation and spoken words in generated caption text.
- Align script tokens to ASR or cue timing, interpolate small homophone or recognition mismatches, and fail the gate when alignment coverage is below `98.5%` or any unmatched script span exceeds `8` tokens.
- Approved WebVTT/SRT/transcript provenance is the source of truth for caption timing and publish packaging.
- Use browser-native WebVTT/TextTrack cue timing for long-form Living Cover captions.
- Keep the locked script and timing source referenced with path/hash. Generated rail VTT/SRT and YouTube sidecars may be packaged with the proof/final only when their manifest records script-locked provenance and QA reads.
- The visible rail caption mirrors the active browser cue into the bottom of the right rail so placement and typography match the fixed video design.
- Display cue-level or phrase-level caption chunks only. Do not use word-by-word karaoke timing.
- Strip diarization prefixes such as `SPEAKER_00:` in display only; do not rewrite the source caption file.
- Match the right rail typography and color system. Do not add Shorts-final visual flare, caption badges, boxes, borders, glows, new accent colors, bouncing, meme styling, or poster-like caption treatment.
- Under `rolling_rail_caption_window_v1`, visible caption text is laid out as script-locked display chunks in a deterministic rolling rail window. The implementation must split long cues with `script_locked_chunk_split_v1`, precompute caption item layout, map `audio.currentTime` or render time to a single `translateY`, and animate only `opacity`, `transform`, and highlight color/alpha. Free-running caption scroll animation, layout-driven jumps, animated font size, max-height, display changes, or DOM reflow-dependent motion are blockers.
- The rolling caption window occupies the middle two-thirds of the fixed right rail safe area. It uses localized background blur and a very subtle translucent fill sampled from the episode backplate behind captions only, plus softened top and bottom mask fades so captions enter and leave naturally. A heavy opaque caption rectangle or full-height right-rail panel is a `tighten` blocker.
- Highlighted phrases are authored in the packet-local `living_cover_cue_map` as exact reviewed key phrase spans. Each span must record phrase text, normalized script token range, timing window, highlight color sample, fade-in duration, fade-out duration, and review status. Highlights may brighten and then fade back as the line scrolls; they must not become karaoke, badges, boxes, glow, or progress indicators. Auto-derived production highlights are blocked; missing reviewed spans keep the packet pending and suppress highlight rendering.
- Review controls, transport chrome, model IDs, QA labels, and internal review copy must remain outside the video frame in review mode and hidden in render/QA mode. The viewer-facing rail may show only the current episode/chapter/beat anchor and the rolling script captions.
- Rolling-caption rough proofs must expose `window.__railCaptionStateAt(time)` and preserve `window.__setRenderTime(time)` so QA can sample start, middle, chapter boundaries, highlight moments, scrub/seek jumps, and end-screen fade behavior without relying on wall-clock animation.
- Final long-form renders must burn visible rail captions into the video frame and preserve the approved VTT sidecar for YouTube upload.
- Publish-readiness packets must record the approved VTT sidecar path/hash, locked script path/hash, timing source path/hash, parse status, cue ordering, and duration match against the approved audio.
- Nothing may use the word `script_literal` unless generated caption text was validated against the locked script itself. Prefer `script_locked`.

## Script-Locked Caption Gate

Every Living Cover visual-system, rough-proof, final-assembly, and publish-readiness manifest must separate caption text provenance from timing provenance:

- `caption_text_source`: locked narration script path/hash.
- `caption_timing_source`: WhisperX JSON, timed VTT, or timed SRT path/hash used only for timing.
- `caption_text_matches_script_read`: `pass` only when normalized generated captions match the normalized locked script after approved nonspoken tag removal.
- `caption_alignment_coverage_read`: `pass` only when script/audio alignment coverage is at least `98.5%` and no unmatched script span exceeds `8` tokens, unless a human-approved deviation ledger is recorded.
- `caption_asr_text_not_used_read`: `pass` only when generated visible text is produced from script tokens, not ASR tokens.
- `caption_known_regression_fixture_read`: `pass` only when known episode fixtures such as Challenger `too weak` versus ASR `two weeks` are asserted against generated output.

Rough-proof, final-assembly, publish-readiness, MP4 render, and YouTube advancement flags must remain `false` when any script-locked caption read is missing or failing.

## End-Screen Policy

`end_screen_hold_read` means static platform target geometry, not identical whole-frame pixels.

- The final YouTube end-screen overlay must keep video target boxes, subscribe targets, safe-zone geometry, and overlay opacity stable after fade-in.
- The default long-form end-screen template is `challenger_titleless_end_screen_overlay_on_living_cover_v1`, proven by Challenger and Therac. It is titleless, has two 16:9 video targets and one center subscribe target, and uses this 1920x1080 geometry: left video `[78,382,758,765]`, right video `[1162,382,1842,765]`, center subscribe `[814,429,1106,721]`.
- A one-video layout, rectangular subscribe button, visible title, separate outro plate, or ad hoc target geometry is a `tighten` blocker unless a human-approved episode override names the template change, source proof, rights/visual rationale, and affected outputs.
- The overlay colors must come from a passing `end_screen_palette_contract`. Source-derived contracts sample or harmonize from the approved episode backplate; overrides must be human-approved and name the reason plus affected outputs. Missing contracts, stale backplate hashes, copied Challenger/default colors, or missing contrast/default-reuse reads block rough-proof keep, final assembly, publish readiness, upload prep, and YouTube action.
- The background motion policy must be explicit in `end_screen_background_motion_policy`.
- Continuous Living Cover ambient motion may continue under the static platform overlay when `continuous_ambient_end_screen_preservation_read` passes.
- Whole-frame hash equality is not a valid end-screen hold requirement when continuous ambient motion is selected; use stable overlay geometry plus differing safe-window background samples.
- Under `rolling_rail_caption_window_v1`, captions continue upward at the approved end-screen transition and then the caption window, localized blur, and all rail caption/highlight text fade to zero. By the YouTube target-geometry window, rail/caption/highlight text must be fully absent.
- Legacy proofs may suppress captions immediately after outro start only when the packet has not adopted the rolling caption model. First-eight successor proofs use the rolling upward exit plus fade-out behavior.
- End-screen visible text is episode-policy-driven. Under `fixed_16x9_right_rail_v1`, end-screen text must stay in the rail or be suppressed unless a human-approved override scopes another surface; static platform target boxes may appear without text. Record `youtube_end_screen_template_read`, `end_screen_title_policy_read`, and `end_screen_text_boundary_read`.
- Viewer-facing chapter, context, caption, cue, rail, and diagnostic text must be fully absent from the YouTube target-geometry window unless the approved end-screen title policy explicitly includes text. Faint residual text is an artifact, not a fade pass. Record `end_screen_text_artifact_read` and `viewer_text_suppression_read`; both fail if text remains visible through low opacity, dark overlays, blend modes, or incomplete rail fade.

## Final Render Contract

Final MP4 renderers must render from the current kept HTML proof, not an older successor-builder script or stale packet.

Render manifests must record:

- `source_html_proof` with packet path, manifest path, player path, and player SHA-256;
- `current_kept_proof_render_source_read`;
- output MP4 path/hash, duration, codec, dimensions, and fps;
- audio policy through `audio_source_encode_read` or `audio_stream_copy_read`;
- `full_decode_read`;
- approved VTT/SRT sidecar path/hash through `caption_sidecar_read`;
- `visible_rail_captions_burned_in_read`;
- `downstream_gate_read` proving publish and YouTube flags remain false after render unless the current phase is explicitly publish-readiness.

Episode bootstrap creates a stable lifecycle review URL at `https://cascadeeffects.tv/reviews/publish-readiness/{episodeId}` and a local lifecycle `review.html` under the episode production tree. The lifecycle manifest starts at `lifecycle_stage: "inception"`, no video, and all upload/publish/visibility locks false. Before final assembly `keep`, the same local review page may refresh to `lifecycle_stage: "in_progress"` and embed the latest reviewable proof/final as a current review artifact, but it must show the active gate, blockers, final assembly disposition, and upload locks. `keep` on an HTML rough proof may open final render only. `keep` on final assembly may open publish readiness only. YouTube upload, publish, schedule, and visibility actions remain blocked until a publish-readiness package exists and explicit human approval is recorded. An unlisted YouTube upload for off-machine cascadeeffects.tv review is still review-only; it does not authorize public or scheduled visibility.

## Publish Readiness HTML Review Contract

Publish-readiness lifecycle and package states must be reviewable as a local HTML page served over a byte-range-capable local HTTP server, not only as Markdown, JSON, or a `file://` page.

The primary review artifact is always `review.html`. In `inception` or `in_progress` lifecycle states it is a status/review hub, not proof of upload readiness. It must:

- embed the final MP4 with native controls served through a byte-range-capable local review server, and the approved upload VTT sidecar as a `<track>`;
- use package-local relative references to copied/staged media assets: final MP4, upload VTT/SRT, thumbnail candidate, QA frames, music/VO transition samples when relevant, and metadata packet;
- display the thumbnail candidate, caption regression frame, VO/music transition sample for music-bearing episodes, and end-screen/safe-window QA frames inline;
- show YouTube metadata, chapter timestamps, tags, audience, category, visibility recommendation, end-screen choices, rights notes, and remaining blockers in the page;
- require title, description, chapter labels, hashtags, and tags to be drafted or QA'd through `/Users/mike/CascadeEffects/ops/agents/skills/youtube_metadata_copywriting_v1/SKILL.md`; record `youtube_metadata_copywriting_read`;
- keep public YouTube metadata copy audience-facing. Title, description, chapter labels, tags, and thumbnail text must not include implementation/workflow language such as `long-form episode`, `publish-readiness`, `proof`, `render`, `sidecar`, `package`, `review surface`, or `upload candidate`; record `public_metadata_copy_read`;
- keep public YouTube tags focused on viewer search intent and episode-central entities. Research-source, scholar, author, or incidental person-name tags are blocked unless named in the public title/description positioning or explicitly approved for discoverability; record `public_tag_relevance_read`;
- show lifecycle stage, current gate, blockers, final assembly disposition when known, and upload-lock state above diagnostics, including `publish_ready: false`, `youtube_upload_ready: false`, `public_release_ready: false`, `may_youtube_action: false`, and `upload_performed: false`;
- use local relative media references from the package location instead of base64-embedding large media;
- record the canonical review URL as `http://127.0.0.1:<port>/review.html` or equivalent local HTTP URL. `file://.../review.html` is allowed as a filesystem path only and cannot satisfy `html_range_server_read` or `html_canonical_review_url_read`;
- keep file paths, hashes, and read values available as evidence without making them the only review surface.

Publish-readiness lifecycle and package manifests must record `primary_review_artifact: "review.html"`, `review_surface_type: "html_inline_media_local_refs"`, `lifecycle_stage`, `current_gate`, `publish_readiness_review_html_path`, `publish_readiness_review_html_sha256`, `publish_readiness_canonical_review_url`, `html_primary_review_read`, `html_media_refs_read`, `html_range_server_read`, `html_canonical_review_url_read`, and `html_upload_lock_read`. Final package manifests additionally record `html_native_video_scrub_read` and `publish_readiness_package_local_asset_copy_read`.

## Remote Publish Readiness Review Contract

The off-machine cascadeeffects.tv review exists from episode inception as a lifecycle hub. Before a reviewable proof/final exists, the remote manifest may omit `assets.video` and render a pending-video state. After a real review video exists, the remote review may attach only an unlisted YouTube upload in the Cascade of Effects channel. Do not upload the final MP4, MOV, M4V, or other large video file to Vercel/Blob.

The remote review manifest must:

- use stable `reviewId = episodeId` so the same URL updates through inception, in-progress review, and final publish-readiness;
- set `lifecycleStage`/`lifecycle_stage` to `inception`, `in_progress`, or `publish_readiness`;
- omit `assets.video` while no review video exists; once attached, set `assets.video.host` to `youtube_unlisted`, with `videoId`, `watchUrl`, `embedUrl`, `privacyStatus: unlisted`, `processingStatus`, `embeddable`, receipt path/hash, and an unlisted-access note;
- upload only small review evidence to remote storage: normalized manifest, metadata packet, caption sidecars, thumbnail candidate, QA frames, and music/VO transition samples;
- record `remote_review_url` as `https://cascadeeffects.tv/reviews/publish-readiness/{episodeId}`;
- record `youtube_unlisted_review_upload_read`, `youtube_unlisted_review_privacy_read`, `remote_review_manifest_read`, and `remote_review_large_video_upload_block_read`;
- keep `publish_ready`, `youtube_upload_ready`, `public_release_ready`, `may_youtube_action`, and public/scheduled visibility false unless a later human approval explicitly changes the gate.

The cascadeeffects.tv route is unlisted and `noindex`, and the YouTube video is unlisted. Anyone with the YouTube watch URL or cascadeeffects.tv review URL may view the video; links must stay limited to reviewers.

Music-bearing publish-readiness manifests must also carry the kept music contract evidence. Required reads are `vo_outro_blend_plan_read`, `vo_outro_music_blend_read`, `vo_outro_perceptual_review_read`, `outro_transition_review_sample_read`, `outro_entry_level_match_read`, `outro_under_vo_masking_read`, `outro_target_after_voice_read`, `outro_prelap_source_read`, `outro_prelap_start_read`, `outro_no_restart_at_voice_end_read`, `outro_source_continuity_read`, and `music_contract_regression_read`. Broad reads such as `full_outro_music_read`, `end_screen_music_handoff_read`, `audio_level_mix_read`, or `music_rights_read` are supporting evidence only and cannot satisfy the VO/outro transition gate. Missing transition samples or subtle-tail reads set the package to `tighten_missing_vo_outro_blend_gate` and block upload prep.

Markdown review packets may remain as historical or support notes, but they are secondary and must point to `review.html` when both exist.

## Caption Waivers

Caption waivers are exceptions, not a normal production path.

- A waiver requires `caption_required: false`, `caption_waiver.override_status: approved`, a human disposition, the reason, and the affected outputs.
- Missing caption files, blocked transcription, or poor cue quality should normally block the gate rather than silently waive captions.
- Waivers apply only to the named episode/package and do not change `living_cover_captioning_process_v1`.

## Motion And Timing

- Preserve deterministic render control through `window.__setRenderTime`.
- Rolling caption proofs must preserve deterministic render control through both `window.__setRenderTime` and `window.__railCaptionStateAt`. Caption scroll position is a pure function of render/audio time, not a free-running CSS animation.
- Rail transition model: staged `120ms / 360ms / 600ms`.
- Phase 1, `0-120ms`: outgoing detail fades or settles while source art holds.
- Phase 2, `120-360ms`: new active title/accent lands and context settles.
- Phase 3, `360-600ms`: new summary/detail fades or translates in.
- Animate only opacity, transform, and accent strength during rail changes.
- Do not animate font size, layout, max-height, display, active-card padding, or rail dimensions.
- Source-art drift/lighting changes, when used, should be delayed or eased so they support the rail transition rather than competing with it.
- Source-art zoom, slide, drift, or lighting states tied to chapter changes must use the Challenger-staged transition model by default rather than swapping transform values at the chapter boundary. The default model is `challenger_staged_visual_transition_v1`: hold the previous source-art state for `0-120ms` after the story boundary, then smoothstep visual mix from `120-600ms`, while rail copy and captions remain inside the fixed right rail.
- Longer cinematic pre-boundary or post-boundary blends require a human-approved visual-system override that names the episode, timing window, reason, affected outputs, and QA reads.
- HTML rough proofs with chapter-driven source-art motion must expose `window.__visualStateAt(time)` or an equivalent render-control hook so QA can verify boundary hold, mix ramp, and settled state.
- Hard-switching source-art `x`, `y`, `scale`, brightness, warmth, or similar state at chapter boundaries is a rough-proof blocker unless a human-approved visual-system override explicitly scopes an abrupt cut.
- If a cold open or montage exists before the first stable Living Cover state, it may start energetic but should visibly settle before the stable rail/story layout lands. Record `cold_open_settle_read` as a review read.
- Successor rough proofs and final renders must check for accidental frozen media, sped-up proof motion, and post-change regressions instead of relying on sparse thumbnails or manifest metadata alone.

## Overrides

Use the default preset unless a specific episode needs a different rail, canvas, or safe-space layout.

An override must record:

- `override_status`: `proposed` or `approved`;
- changed field path, such as `rail.width_px` or `type_scale.active_title_px`;
- reason for the change;
- visual or computed QA evidence;
- human disposition: `keep`, `tighten`, or `reject`;
- whether the override is episode-local or proposed as a new preset.

No override is active until it is human-reviewed. If approval is ambiguous, keep `override_status: proposed` and downstream flags false.

## Required Reads

Future visual-system, rough-proof, and final-render packets using this spec should include the applicable reads below. Use `not_applicable` when the packet has no rendered media stream, no predecessor comparison, no cold open, or no final end-screen window; do not invent placeholder evidence to force a read.

- `living_cover_system_version_read`
- `captioning_process_version_read`
- `fixed_16x9_canvas_read`
- `browser_shell_letterbox_read`
- `source_art_carrier_read`
- `video_visual_style_scope_read`
- `paper_architecture_visual_style_read`
- `foreground_admin_prop_read`
- `implied_action_anticipation_read`
- `ambient_affordance_read`
- `generation_tool_provenance_read`
- `procedural_signal_overlay_read`
- `ambient_line_artifact_read`
- `end_screen_palette_contract_read`
- `end_screen_target_fill_palette_read`
- `end_screen_target_contrast_read`
- `rail_panel_palette_read`
- `source_integrated_panel_color_read`
- `no_cross_episode_default_palette_read`
- `right_rail_safe_space_read`
- `viewer_text_surface_inventory_read`
- `right_rail_text_boundary_read`
- `out_of_rail_text_read`
- `ordinal_chapter_label_read`
- `end_screen_text_boundary_read`
- `living_cover_cue_map_read`
- `chapter_cue_coverage_read`
- `typography_cue_read`
- `effect_map_cue_read`
- `source_safe_motion_read`
- `cue_no_diagnostic_overlay_read`
- `cue_map_internal_artifact_read`
- `visible_cue_overlay_read`
- `ambient_effects_plan_read`
- `ambient_effect_lane_decision_read`
- `source_plate_matte_registration_read`
- `foreground_occlusion_read`
- `effect_layer_source_safety_read`
- `deterministic_ambient_read`
- `additive_effect_integration_read`
- `debug_overlay_absence_read`
- `ambient_effect_browser_sample_read`
- `range_scrub_effect_review_read`
- optional per-effect reads such as `localized_particle_density_read`, `particle_foreground_leak_read`, `public_motion_occlusion_reappearance_read`, `practical_light_micro_life_read`, and `screen_glow_motion_read`
- `music_integration_plan_read`
- `series_music_contract_read`
- `approved_music_source_read`
- `intro_music_contract_read`
- `voice_start_offset_read`
- `caption_timing_shift_read`
- `full_outro_music_read`
- `end_screen_music_handoff_read`
- `vo_outro_blend_plan_read`
- `vo_outro_music_blend_read`
- `vo_outro_perceptual_review_read`
- `outro_transition_review_sample_read`
- `outro_entry_level_match_read`
- `outro_under_vo_masking_read`
- `outro_target_after_voice_read`
- `outro_prelap_source_read`
- `outro_prelap_start_read`
- `outro_no_restart_at_voice_end_read`
- `outro_source_continuity_read`
- `audio_level_mix_read`
- `music_rights_read`
- `music_contract_regression_read`
- `no_music_or_temp_music_waiver_read`
- `rail_preset_read`
- `rail_content_model_read`
- `caption_display_model_read`
- `caption_window_role_read`
- `caption_window_treatment_read`
- `caption_highlight_source_read`
- `caption_palette_source_read`
- `no_responsive_rail_reflow_read`
- `no_rail_scale_hack_read`
- `chapter_label_legibility_read`
- `active_beat_title_legibility_read`
- `summary_legibility_read`
- `context_legibility_read`
- `old_context_rows_absence_read`
- `minimal_anchor_read`
- `copy_hierarchy_read`
- `current_context_deduplication_read`
- `native_caption_behavior_read`
- `rolling_caption_behavior_read`
- `rolling_caption_state_hook_read`
- `caption_scroll_smoothness_read`
- `caption_window_fade_mask_read`
- `caption_window_transparency_read`
- `caption_key_phrase_span_read`
- `caption_highlight_fade_read`
- `caption_end_screen_rollout_read`
- `caption_required_read`
- `caption_output_model_read`
- `caption_text_source_read`
- `caption_timing_source_read`
- `caption_text_matches_script_read`
- `caption_alignment_coverage_read`
- `caption_asr_text_not_used_read`
- `caption_known_regression_fixture_read`
- `caption_phrase_level_read`
- `no_karaoke_caption_read`
- `rail_typography_match_read`
- `caption_bottom_rail_fit_read`
- `caption_spacing_read`
- `caption_no_embellishment_read`
- `caption_vtt_reference_read`
- `caption_sidecar_preservation_read`
- `caption_waiver_read`
- `transition_staging_read`
- `challenger_staged_transition_model_read`
- `first_chapter_boundary_visual_ease_read`
- `chapter_boundary_hard_shift_read`
- `focused_transition_review_strip_read`
- `visual_state_debug_hook_read`
- `cold_open_settle_read` when a cold open or montage exists
- `stale_cross_episode_label_read`
- `visual_freeze_read`
- `proof_speedup_read`
- `post_change_regression_read`
- `current_kept_proof_render_source_read`
- `audio_stream_copy_read` for visual-only variants
- `audio_source_encode_read` when the approved audio source must be encoded into the final MP4 container
- `video_stream_copy_read` for audio-only variants
- `caption_sidecar_read`
- `visible_rail_captions_burned_in_read`
- `downstream_gate_read`
- `full_decode_read`
- `end_screen_hold_read`
- `continuous_ambient_end_screen_preservation_read`
- `youtube_target_geometry_static_read`
- `end_screen_title_policy_read`
- `end_screen_text_artifact_read`
- `viewer_text_suppression_read`
- `youtube_metadata_copywriting_read`
- `public_metadata_copy_read`
- `public_tag_relevance_read`
- `caption_suppression_read`
- `rail_fade_read`
- `final_luma_drop_read`
- `youtube_end_screen_safe_zone_read`
- `full_frame_dark_overlay_read`
- `localized_readability_treatment_read`
- `no_progress_bar_read`
- `no_timecode_read`
- `gradient_vignette_read`
- `copied_media_read`
- source-art reads required by the active visual system, including `texture_noise_read` when generated/source artwork is used.

## QA Requirements

Every HTML rough proof and downstream render using this system must produce or record the applicable items:

- JSON manifests that parse with `jq empty`;
- fixed stage design size `1920x1080`;
- `16:9` stage and frame aspect ratio;
- no responsive media query affecting rail/text layout;
- no transform `scale()` on rail, active panel, chapter label, active title, summary, context list, context row, dot, or context title;
- computed typography checks for chapter label `26px`, active title `64px`, summary `34px`, and context titles `28px`, unless an approved override exists;
- computed caption checks for rolling middle-rail placement, `40px` caption type, fixed metrics, stable transform/opacity motion, rail-native/source-sampled colors, no overlap with the minimal top anchor, and no visible diarization prefix;
- static caption checks for deterministic audio-time rolling behavior, `window.__railCaptionStateAt(time)`, preserved `window.__setRenderTime(time)`, no free-running scroll animation, no word-by-word karaoke engine, script-locked text provenance, timing-only ASR provenance, and no caption card/badge/border/glow/accent embellishment;
- script-locked caption checks proving normalized generated caption text equals normalized locked script text, alignment coverage is at least `98.5%`, no unmatched script span exceeds `8` tokens, ASR words are not used as output text, and known homophone fixtures such as `too weak` versus `two weeks` stay script-locked;
- rail-label checks proving active right-rail copy is episode-specific, viewer-facing, and free of stale cross-episode/internal labels;
- viewer-text boundary checks proving all visible story/chapter/caption/effect/end-screen text is inside the fixed right rail, no out-of-rail text surfaces are present, and no ordinal-only chapter labels appear as visible copy;
- cue-map checks proving every major chapter has a planned source-safe cue, key phrase typography and effect-map moments are present at the approved cadence inside the rail or as non-textual behavior, rolling caption highlight spans record phrase text/token range/timing/color/fade/review status, and photoreal/source-preserving proofs do not add diagnostic overlays or out-of-rail text panels over source art;
- ambient/effects checks proving every episode has an explicit lane decision, source/matte registration and foreground occlusion are correct when needed, deterministic parameters are recorded, successor effects preserve prior layers, browser/range samples exercise the active effects, and no debug overlays or effect labels appear in viewer-facing output;
- music integration checks proving every episode has an explicit music contract or human-approved waiver, approved source paths/hashes and rights notes are recorded, voice-start offset and fade/outro policy match the series/episode contract, captions/chapters/story time are retimed when needed, full outro music carries the end-screen window, the final VO-to-outro transition passes perceptual blend review with a transition sample and level-match notes, and the under-opening-voice plus short-tail regression is absent when matching Challenger;
- end-screen palette checks proving `end_screen_palette_contract` exists once a backplate is approved, the recorded backplate hash matches the approved source, target fill/border/subscribe/text/accent values are sampled or harmonized from the backplate unless a human-approved override names the affected output, contrast/readability reads pass, and Challenger/default colors are not copied across episodes;
- final-render caption checks for visible rail captions burned into the MP4 and approved VTT sidecar preserved for YouTube upload;
- publish-readiness caption checks for VTT parse success, ascending cue times, and cue timing aligned to the approved audio duration;
- publish-readiness HTML checks proving `review.html` exists, package-local media references resolve, the final MP4 is embedded with native controls, the page is served through a byte-range-capable localhost URL, the approved upload VTT sidecar is attached with a `<track>`, thumbnail, QA frames, and VO/outro transition samples render inline, and upload/publish flags remain visibly locked;
- publish-readiness metadata checks proving public title, description, chapter labels, tags, and thumbnail text are audience-facing and free of internal workflow language;
- publish-readiness copy checks proving title, description, chapter labels, hashtags, and tags were drafted or QA'd through `youtube_metadata_copywriting_v1`;
- publish-readiness tag checks proving public tags are viewer-facing search intents or episode-central entities, not leaked research-source, scholar, author, or incidental person-name tags;
- rough-proof and final-render manifests must record source path, source role, SHA-256, stream count, codec, duration, and decode status for every rendered media source;
- generated source-art and motion carriers must record explicit `generation_provenance` with tool, model, confidence, mode, source-generation path/hash, final asset path/hash, and prompt/init/reference provenance where applicable;
- visual-only variants must preserve or copy the audio stream and record `audio_stream_copy_read`; audio-only variants must preserve or copy the video stream and record `video_stream_copy_read`;
- successor proofs and finals must record `visual_freeze_read`, `proof_speedup_read`, and `post_change_regression_read`;
- final renders must record `source_html_proof`, `current_kept_proof_render_source_read`, `full_decode_read`, duration, codec, dimensions, fps, audio encode/copy policy, caption sidecars, visible rail caption burn-in, and downstream gate state;
- final renders must hold static platform target geometry during the YouTube overlay window, explicitly record background motion policy, and record `end_screen_hold_read`, `youtube_target_geometry_static_read`, `continuous_ambient_end_screen_preservation_read` when ambient motion continues, `end_screen_title_policy_read`, `caption_suppression_read`, `caption_end_screen_rollout_read`, `rail_fade_read`, `final_luma_drop_read`, and `youtube_end_screen_safe_zone_read`;
- end-screen QA must detect faint residual viewer text as a failure, not a fade pass. Verify computed opacity/visibility or pixel evidence for chapter, context, caption, cue, rail, and diagnostic text surfaces; record `end_screen_text_artifact_read` and `viewer_text_suppression_read`;
- no full-frame dark veil may be used as the default readability solution over approved source art; record `full_frame_dark_overlay_read` and `localized_readability_treatment_read` when readability treatment is present;
- Paper Architecture material QA applies only to allowed website, YouTube channel-brand, and website thumbnail-gallery surfaces; for long-form video assets, Paper Architecture resemblance itself blocks advancement;
- screenshots at `1920x1080`, `1280x720`, `320x180`, `168x94`, and at least one tall and one wide non-16:9 browser shell;
- no copied `.mp4`, `.mov`, `.wav`, `.mp3`, `.srt`, or `.vtt` files inside HTML proof packets;
- all downstream MP4/final/Shorts/publish/YouTube flags defaulting `false`.
