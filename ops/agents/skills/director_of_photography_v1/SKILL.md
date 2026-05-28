---
name: "director_of_photography_v1"
description: "Design reusable Cascade Effects Shorts shot packets with sub-beat IDs, timing, camera language, motion coverage, and reuse-vs-scout decisions."
---

# Director Of Photography v1

Use this skill when a Cascade Effects YouTube Short needs cinematography planning after visual research or after a motion proof fails because a shot is too long, too static, slow, jittery, or stretched. During the Challenger-first restart, it also owns workflow scope approval, DP research briefs, the research-driven visual beatmap, exact legacy imports, and the active episode constraint ledger.

This skill is a specialist called by the Shorts coordinator:

- [/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md)

It designs the shot sequence and controls which visual constraints may become active. It does not render stills, render motion, promote visual assets, revise audio, revise scripts, or export finals.

## Long-Form Boundary And Visual Lesson Imports

Long-form Living Cover, backplate, source-art, fixed right-rail, visual-system baseline, and publish-readiness visual requests route to [/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/long_form_video_production_v1/SKILL.md), not to DP shot planning. The long-form skill owns the episode visual-system baseline index and the active backplate rules learned from Challenger, Therac-25, Hyatt Regency, Tacoma Narrows, and successors.

DP may use those long-form outcomes as taste references only. They do not become active Shorts constraints unless the current workflow scope manifest imports the exact artifact or rule and the active episode constraint ledger approves it.

The cross-workflow visual lesson is: do not solve generated image prompts with foreground clipboards, binders, folders, paperwork stacks, or generic administrative props. Those objects usually create static evidence-table compositions instead of visual anticipation. Use them only when the current scoped episode names the exact object as mechanism-critical, keeps it out of the dominant foreground read, and records the exception in the active ledger. Prefer implied action, anticipation, subject/event presence, layered depth, right-rail or caption-safe negative space when relevant, and visual structures that can support ambient effects such as screen glow, practical lights, weather, crowd attention, machinery readiness, or subtle public-scene motion.

## Challenger-First Restart Contract

Production is restarted from Challenger first. All existing visual constraints, old renders, model experiments, keeper registry lessons, casebook lessons, old manifests, packaging rules, and previous episode constraints are legacy by default.

Before visual research or still generation, the DP must produce or approve:

- `workflow_scope_manifest`, from [templates/workflow_scope_manifest_template.md](templates/workflow_scope_manifest_template.md)
- `dp_research_brief`, from [templates/dp_research_brief_template.md](templates/dp_research_brief_template.md)
- `archival footage review`, from [templates/archival_footage_review_template.md](templates/archival_footage_review_template.md), whenever archival motion is in scope
- `visual beatmap`, derived after research
- `episode_constraint_ledger`, from [templates/episode_constraint_ledger_template.md](templates/episode_constraint_ledger_template.md)

Use [references/dp_research_constraint_policy.md](references/dp_research_constraint_policy.md) as the governing policy and [references/restart_constraint_audit_challenger_hyatt_therac_737.md](references/restart_constraint_audit_challenger_hyatt_therac_737.md) as the baseline audit. The active ledger is the only source of visual constraints for the scoped short. Prior Challenger, Hyatt, Therac, 737, casebook, keeper, and model-experiment rules are not active unless the DP imports and activates an exact rule or file in the current ledger.

## Intent

Translate an approved Short script and approved audio timing into a research-driven shot-level production plan that a visual research or stills agent can execute without inventing editorial coverage. The plan should feel like a director of photography and editor solved the coverage problem before image generation begins.

The DP skill is mandatory when feedback says:

- one generated clip holds too long
- motion is slow, jittery, stretched, or too static
- a beat needs more than one shot
- a long narration span needs sub-beats
- a motion proof should be rebuilt from multiple native-duration handles

## Required Inputs

Use available local artifacts before asking for more information.

- `episode_id` and `short_id`
- approved Short script path
- approved audio duration, caption timing file, or cue ranges
- current narration map, if one exists
- archival footage review path, if archival motion is in scope
- current visual beatmap, if one exists
- production model decision path, if visual research is complete
- workflow scope manifest path
- DP research brief path
- active episode constraint ledger path
- visual research packet path, if one exists
- existing approved stills and motion paths, if any
- current blockers from stills, motion, or final QA
- active episode constraints from the current DP-approved ledger
- known physical dimensions, scale references, custody/access constraints, or source URLs for real objects that appear in the shot, when available

If timing is missing, derive provisional shot timings from the approved audio transcript or caption timing and mark them `needs timing confirmation`. Do not invent a new script.

If scope manifest, research brief, or active ledger is missing, return `tighten` and create the missing DP artifact before allowing visual research or still generation.

## Output Contract

Produce a formal `shot_plan_v2` packet, usually from [templates/dp_shot_packet_template.md](templates/dp_shot_packet_template.md).

Every shot must include:

- stable `shot_id`, using sub-beat IDs such as `beat_04a`, `beat_04b`, `beat_04c`
- source `visual_beat_id`
- exact `start_seconds`, `end_seconds`, and `duration_seconds`
- narration phrase covered
- editorial purpose
- composition, lens/framing, lighting, palette, and camera logic
- `coverage_class`
- `engagement_goal`
- `mechanism_visibility_rule`
- `coverage_exception_approved`
- `preferred_clip_ids`, `backup_clip_ids`, `footage_family_id`, `archive_reference_mode`, `texture_influence`, `historical_context_year_or_range`, `source_media_era`, `historical_signal_profile_id`, `signal_texture_strength`, `texture_application_scope`, and `youtube_survival_required` when archival or period-media-derived motion is in scope
- `motion_source_preference`: `direct_source_clip|source_derived_reanimation|direct_source_still|still_driven_i2v|generated_still|hybrid_generated`
- `still_generation_required`: `true|false`
- source-derived reanimation fields when used: `source_clip_id`, `source_span_in`, `source_span_out`, `start_keyframe_path`, `end_keyframe_path`, `same_camera_span_required`, and `reanimation_backend`
- `scroll_stop_priority`, `continuity_vector`, `coverage_budget_role`, and `source_or_generation_reason`
- movement and transition
- prompt-ready still concept
- literal vs representational status: `literal object`, `cut sample/coupon`, `subscale test article`, `administrative carrier`, `metaphor`, or `composite`
- physical scale check: known object dimensions or scale relationships, plus whether the proposed framing makes them plausible
- custody/access/scene feasibility: why the object or scene could plausibly be present in the depicted place
- scale source paths or URLs, when known
- scale or custody blockers that must be repaired before visual research
- reuse decision: `reuse approved still`, `reuse with crop/timing`, `fresh scout pass`, or `new full render`
- scout priority and rationale when a fresh scout is required
- motion strategy with native handle target and maximum allowed stretch
- visual risks and banned elements

The packet must also include:

- paths to workflow scope manifest, DP research brief, narration map, visual beatmap, episode constraint ledger, source script, audio/timing, visual research, and exact DP-approved imports
- archival footage review path when archival motion is in scope
- production model decision path and selected `production_model_lane`
- editorial spine brief naming 2-4 hero source families, source-family budget, room/admin/process coverage cap, continuity vector, and any subject/event imagery that outranks literal narration coverage
- total shot count
- longest shot duration
- any shot longer than 6 seconds and why it is allowed
- physical plausibility summary covering scale, custody, and literal-vs-representational decisions
- active constraint summary and any legacy constraints explicitly retired or imported
- render authorization assumptions for each shot: whether a sourced still/clip, source-derived reanimation, or generated still is actually required
- blockers and next required stage

## DP Rules

- Prefer 3-5 second shots for Shorts.
- Split any narration span longer than 6 seconds into multiple shots unless the stillness is intentional and documented.
- When motion proof feedback says some story shots are too brief, too long, repetitive, or logically disconnected, stop solving at the beat-handle level and create a shot-level timing EDL. Each actual story shot should have its own `shot_id`, parent beat, source path/span, intended and actual duration, and hidden-cut read. Normal story shots must be at least `2.0` seconds unless an explicit later rule changes the floor.
- Before any motion video proof, require a shot-level timing EDL. Beat-level handles and beat-rollup sheets are review aids, not proof-edit authority.
- Treat source-native camera cuts as real story cuts. They must either appear as their own EDL rows or be avoided by choosing a cleaner source span or a stable source-frame hold. Do not let a five-second microsequence hide sub-second source flashes.
- Distinguish diagnostic motion handles from proof-minded edit timing. Five-second handles are useful for model/candidate review; once a shot-level timing EDL is active, the edit should follow the approved audio timing and the `2.0` second story-shot floor instead of forcing every visible story unit to five seconds.
- For moving-subject sequences, especially launch, ascent, vehicle failure, machinery motion, clinical procedure motion, and disaster motion, plan a continuity vector before choosing spans. Do not cut from a subject gaining altitude, distance, damage, or process progression back to a lower/earlier/geographically reset view unless the EDL marks an intentional time reset.
- Avoid editorial flashes. Fades, source-native transitions, or quick inserts that make an image appear for less than the declared story-shot floor must be split into explicit EDL rows or removed.
- If a human review says the repaired edit is not materially different, stop micro-adjusting. Rebuild the editorial spine: fewer source families, clearer before/after logic, stronger hero motion, and less beat-literal room/process coverage.
- Apply the Shorts scroll test when choosing carriers and timing. If a viewer scrolling YouTube Shorts would choose a gorgeous subject/event image over a boring hearing room, control room, admin table, or process shot, the DP should choose the subject/event image and let narration carry the causal detail. Institutional room coverage is context, not the default carrier, unless it is itself the strongest visual.
- Do not plan Paper Architecture as a Shorts visual style. Paper Architecture belongs only to CascadeEffects.tv website assets, YouTube channel-level branded visual assets, and CascadeEffects.tv website thumbnail-gallery images. For Shorts shot plans, reject `cascade-paper-architectures-ink-lit-v1`, folded-paper/foam-core source art, paper-model tableaux, or Paper Architecture resemblance for stills, keyframes, motion, proof frames, final frames, cover frames, in-video graphics, or thumbnails.
- Use the production model decision to stay source-first and cost-aware. If the chosen lane is `source_led_motion` or `source_derived_reanimation`, do not plan generated stills unless a shot records why approved source material fails and generation is the cheapest path to the intended result.
- Avoid stretching generated motion above roughly `1.25x`.
- Use straight cuts by default; use restrained dissolves only when the cut would create incoherent geography.
- Treat each shot as one clean visual idea.
- Prefer locked documentary frames, believable lens perspective, and controlled light motion.
- Use motion carriers that are easy for image-to-video models to preserve: light sweep, monitor glow, vapor drift, focus settle, indicator flicker, slight parallax, or clean camera creep.
- Do not lock the final visual beat structure before research. The narration map is causal/timing input only.
- The DP must apply the `engaging and visually stimulating` thesis during artifact selection and beatmap design, not just prompt writing.
- For disaster, launch, machinery, clinical, transportation, or other event-forward episodes, rank hero subject/event footage above room/process coverage when both can carry the same narration span. Record `scroll_stop_priority: subject_event` or an explicit `scroll_stop_exception_approved` when choosing lower-energy room coverage.
- Keep the editorial spine portable across episodes: choose source families by role and visual power, not by Challenger-specific subject names. For example, record `hero_event_footage`, `institutional_context`, or `mechanism_process` roles rather than making shuttle imagery a global rule.
- Treat foreground clipboards, binders, folders, paperwork stacks, and generic admin props as low-energy default carriers. They are `tighten` unless the shot records why that exact object is mechanism-critical, why a room, subject, event, role-based human scene, or active equipment carrier would weaken the beat, and how the composition still creates implied action or anticipation.
- When handing a shot plan into the stills-contact-sheet stage, the DP should expect the default review surface to show raw full-frame clean candidates with beat info visible directly on the sheet as minimal plain-text labels only. Do not plan around bordered tiles, blurred fills, padded presentation cards, or sidecar-only beat mapping.
- When archival motion is in scope, the DP must complete the archival footage review before the beatmap is locked.
- Archival motion is `hybrid` by default for this pass. Keep the archival source pool narrow: up to `3` primary videos plus up to `2` backups.
- Under `strict clean`, any visible logo, stinger, lower-third, watermark, burned caption, end card, split screen, or channel bug is an automatic archival reject. Do not plan crop or cleanup fallback.
- Multiple narration lines may share one strong archival footage family. Stop literal one-line-one-image mapping when the footage family is stronger.
- Prefer sourced coverage first in planning, but keep stage semantics straight: once a beat enters `motion contact sheet`, the default motion-test input is the approved still-stage source surface for that beat. If a direct source clip already solves the beat, route that clip through a separate `source motion scout` or `source clip approval` artifact instead of replacing the motion-contact-sheet still inputs. Use `generated_still` only when no approved sourced clip or still already gives you the shot.
- Treat `source_derived_reanimation` as the preferred middle lane when an archival motion span has the right subject, texture, and camera language but the edit needs a different duration, cadence, or beat emphasis. The DP must choose the source span and keyframe family before motion rendering starts.
- For launchpad, shuttle-on-pad, plume, rigid machinery, or other physics-sensitive historical beats, do not ask still-driven motion to invent ignition, liftoff, plume growth, structural deformation, or other event-level changes that are not already present in the approved source still. Prefer direct sourced archival motion for those beats when clean source footage exists.
- If a launch/ascent beat still needs LTX-generated motion, plan it as same-camera source-derived keyframe interpolation: real clean archival start frame, real clean archival end frame, consistent crop/scale, and no cross-angle keyframes. Do not plan single-still I2V for ignition, liftoff, plume growth, ascent, or explosion-scale event motion.
- For human, clinical, office, courtroom, control-room, or role-based historical scenes, plan source-derived reanimation as low-amplitude motion unless the clean source span supports larger action. Preserve subject count, posture, role, room layout, equipment position, and camera setup; do not plan invented medical action, sit/stand behavior, people entering/leaving, or facial identity changes.
- When a full-bleed vertical archival crop makes the source visibly soft or blocky, plan a conservative `archival_cleanup_scout` before asking motion or proof stages to use cleaned footage. The DP should record the source math (`source_resolution`, `crop_width_px`, `upscale_factor`) and keep full-bleed `9:16`; do not solve source weakness with pillarboxes, mattes, AI super-resolution, face smoothing, synthetic detail, or a global modern-HD look. If the conservative scout cannot pass without artifacts, route the affected beat to better archival source search.
- For Challenger, literal technical/evidentiary coverage is support-only: one insert-heavy beat family or two insert shots total unless the DP records an override.
- `texture_influence` values are `none|house_crt`. For active Shorts, plan `house_crt` for story clips that enter proof/final unless the coordinator records an explicit waiver.
- When `texture_influence: house_crt` is planned, use the Challenger-calibrated `era_1980s_broadcast_crt_v1` profile at `visible_but_premium` as the cross-episode house clip texture. Do not choose film grain, institutional-video, 1990s-news, 2000s-web, or mobile-video texture by episode period/source medium. Plan randomized TV static/noise only between story clips as transition material; it is not a continuous overlay and not an excuse to hide weak cuts, weak motion, or failed hygiene.
- Prefer scene-led coverage first, mechanism inserts second, and low-energy admin-detail carriers only when no stronger researched option survives.
- `technical_insert` and `admin_detail` are exception classes for Challenger. They require `coverage_exception_approved: true` plus a note explaining why a room, exterior, vehicle, or role-based human scene would weaken the beat.
- Do not inherit bans or allowances from old constraints. Generated hands, readable documents, labels, mission patches, UI screens, wall text, diagrams, posters, caption-like surfaces, logos, or text rules must come from the current active ledger before they control prompts.
- Captions are final-export only. Do not design caption-safe bands into generated stills or motion prompts.
- Run a physical plausibility check before a shot can leave DP planning. Ask: how big is the real object, could it fit in this frame or container, and would it plausibly be in this room or custody state?
- Do not turn large, hazardous, continuous, classified, inaccessible, or one-off historical components into small tabletop props. Use a verified cut segment, test coupon, subscale article, or administrative carrier instead, and label that status in the shot plan.
- Do not use "small versions" of real components as visual metaphors unless the plan says they are a model, test sample, or non-literal representational object and visual research can support that claim.
- If physical scale, custody, or scene feasibility is uncertain, mark the shot `tighten` and route back before visual research or still generation.
- Do not read from `/archive/`, `/archives/`, `/experiments/`, `/legacy/`, `/retired/`, `/midjourney/`, `/proof_stills/`, diagnostic outputs, mixed-review outputs, old renders, old manifests, or old casebook/keeper-derived constraints unless the workflow scope manifest lists the exact DP-approved import path.
- If useful legacy material is discovered, stop and record a DP import before using it.

## Reuse And Scout Decisions

Use `reuse approved still` when an existing keeper already carries the subject, composition, and motion risk profile.

Use `reuse with crop/timing` when a keeper still is correct but needs a different duration, crop, or order in the edit.

Use `fresh scout pass` when the shot family, lens, subject scale, or coverage role is new and should be tested with a small A/B scout before a full stills/keyframe contact sheet.

Use `new full render` only when the shot is already well specified and belongs in the next full contact sheet rather than a scout.

If a shot exists only to repair a failed motion proof, prefer fresh scout passes for the most motion-brittle shots instead of asking motion to repair a weak still.

## Handoff Shape

Return a stage-aware packet:

```yaml
stage: dp shot planning
episode_id:
short_id:
workflow_scope_manifest_path:
dp_research_brief_path:
narration_map_path:
visual_beatmap_path:
episode_constraint_ledger_path:
shot_plan_v2_path:
source_context: [source_writer_packet_path, source_longform_script_path, longform_fact_check_report_path, short_script_path]
audio_context: [short_audio_wav_path, caption_source_path, caption_timing_path, approved_audio_duration_seconds]
visual_context: [visual_research_packet_path, preferred_artifact_ids, exact_dp_imports, existing_approved_stills, existing_approved_motion]
production_model_context: [production_model_decision_path, production_model_lane, hero_source_family_ids, source_family_budget, render_authorization_read]
archival_context: [archival_footage_review_path, footage_family_ids, preferred_clip_ids, archive_reference_modes, texture_influence]
motion_source_context: [motion_source_preference, still_generation_required, source_derived_reanimation_spans, keyframe_requirements]
constraint_context: [active_constraint_ids, conditional_constraint_ids, legacy_reference_ids, retired_constraint_ids]
shot_count:
shots_reusing_approved_stills:
shots_requiring_fresh_scout:
physical_plausibility_summary:
motion_strategy_summary:
disposition: keep | tighten | diagnostic only | reject
blockers:
next_action:
may_advance: true | false
```

Only the coordinator may treat `may_advance: true` as production advancement.

## Edge Cases

- If the Short script is not approved, route back to `script`.
- If audio is not approved or timing is unknown, route back to `audio` or produce only a diagnostic timing draft.
- If workflow scope, DP research brief, or active constraint ledger is missing, route back to the DP-owned missing artifact before visual research.
- If a narration map exists but the visual beatmap has not yet been derived from research, do not treat the narration map as the canonical beat spine.
- If visual research is complete but the production model decision is missing, stale, or fails to choose a lane, stop before visual beatmap lock.
- If archival motion is in scope and the archival footage review is missing, stale, exceeds the narrow source cap, lacks exact local paths, or has unresolved hygiene failures, stop before beatmap lock and route back to the archival review.
- If a visual research packet already exists but the new DP plan adds shot families, mark the packet stale and route back to `visual research packet`.
- If the DP plan cannot name hero source families or a continuity vector, return `tighten` and create the editorial spine brief before any render stage.
- If research artifacts are weak, repetitive, or low-energy, rerun research and the visual beatmap before widening shot coverage.
- If a sourced or hybrid archival reference leaks logos, stingers, lower-thirds, channel bugs, or burned captions into generated output, classify that as `absorbed archival contamination` and reopen the carrier or source span instead of tightening wording.
- When motion candidates come back, the DP must review the actual MP4s before coordinator handoff. Dense frame sampling is required for every clip, and launchpad-, plume-, vehicle-, rigid-geometry-, or machinery-led clips require frame-by-frame or near-frame-by-frame inspection. If the clip invents a different event than the source shot, record it as a reject and reroute the beat instead of spending another motion pass on the same still.
- If all proposed shots require new visual language, require a 2-3 shot scout before a full stills/keyframe contact sheet.
- If a failed motion proof only needs a timing edit and all shots are already good, do not invent new shots.
- If a proposed object fails the scale/custody check, replace it with a physically plausible carrier before visual research. Example: a full Shuttle SRB field-joint O-ring cannot become a small tray object; only a verified cut seal segment, test coupon, subscale article, or non-object administrative carrier may appear at tabletop scale.
- If a request asks for long-form video, Living Cover, backplate, source-art, fixed right rail, or episode visual-system baseline work, return `tighten` only as a routing disposition and hand off to the long-form video production skill. Do not state that long-form video production is inactive.

## Example

See [examples/challenger_restart_shot_plan_v2.md](examples/challenger_restart_shot_plan_v2.md) only as a legacy reference example for `challenger_short_restart_v1`. New Challenger production must use a new scoped short root and active ledger before visual research.
