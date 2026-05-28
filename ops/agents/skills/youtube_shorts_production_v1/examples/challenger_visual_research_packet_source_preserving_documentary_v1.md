# Visual Research Packet - challenger_short_minimal_surreal_v3_trimmed

Restart note: this is a legacy example. It must not be used as active Challenger visual research, prompt constraint source, or still-generation input unless the DP imports this exact file in the workflow scope manifest and activates specific constraints in the current episode constraint ledger.

## Packet

- `episode_id`: `challenger`
- `short_id`: `challenger_short_minimal_surreal_v3_trimmed`
- `short_script_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/challenger_short_v3_trimmed.txt`
- `narration_map_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/narration_map.md`
- `visual_beatmap_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/shorts/challenger_short_v3_trimmed/production/short_beat_shot_plan.md`
- `cue_ranges_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_short_v3_trimmed/transcripts_mastered/challenger_short_v3_trimmed.diarized.txt`
- `caption_source_path`: `/Users/mike/Audio_CascadeEffects/tmp/ep1_challenger_short_v3_trimmed/transcripts_mastered/challenger_short_v3_trimmed.diarized.txt`
- `audio_package_sha256`: `1e191295642fd5dc2bb3d98c306da7cf09962b2e1d654933d9f9fc9a97160c36`
- `transcript_sha256`: `4c849f6aa47bd00ec64d6bf020d3b9253994484385d04367bfa12de0fd9dbf7c`
- `style_skill_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/SKILL.md`
- `subject_render_matrix_path`: `/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/judgment/subject_render_matrix.md`
- `disposition`: `keep`
- `blockers`: `none`

## Research Rules

- Use references as constraints for subject identity, mechanism clarity, materials, setting, camera logic, and palette.
- Do not copy a reference image, artist style, logo, readable archival text, UI, poster, or caption design into generated stills.
- Keep research mechanism-led; a mood note alone is not enough to authorize still generation.
- In the current flow, each beat must also declare a recognizable source anchor and an anchor-preservation rule before still generation may begin.
- Name missing evidence as a deferred gap instead of inventing visual certainty.

## Source Set

- `source_inventory_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/visual_research/source_inventory.json`
- `research_notes_path`: `/Users/mike/Episodes_CascadeEffects/Ep1_Challenger/visual_research/sources.md`
- `active_short_manifest_path`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_minimal_surreal_v3_trimmed.json`
- `primary_style_package`: `source_preserving_documentary_v1`
- `reference_use_policy`: `Use source paths and IDs to constrain subject geometry, materials, era, and camera logic. Do not copy captions, labels, NASA marks, UI overlays, or archival text into generated visuals.`

## Beat Research

### `beat_01a`

- `cue_range`: `00:00:00.031-00:00:05.958`
- `narration_excerpt_or_transcript_range`: `[00:00:00.031-00:00:05.958] The night before Challenger launched, Roger Boisjoly told NASA not to fly. He had the data.`
- `mechanism_claim`: `A known technical warning exists before launch, but the frame should hold the warning inside the launch system rather than turn it into a courtroom or lecture image.`
- `primary_subject`: `engineer proxy at an upper-tower side terminal with the orange external tank filling the exterior background`
- `canonical_subject_constraints`: `One human figure, upright or leaning into a terminal, must remain secondary to the shuttle-tower context. The exterior must read as external tank/launch structure, not a generic spacecraft or office window.`
- `historical_or_domain_reference_notes`: `Use Challenger pad/tower and tank references from the existing visual research lane; this beat should feel like a warning inside launch infrastructure, not a generic NASA control room.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/launch_stack_exterior/selects/launch_stack_exterior.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/ice_on_pad_gantry/selects/ice_on_pad_gantry.png; source IDs act3_06, act3_07, act3_08`
- `palette_material_constraints`: `Cold blue-gray gantry steel, muted orange external tank, off-white terminal glow, low-saturation documentary light.`
- `camera_logic`: `Medium vertical tower-side frame; figure and terminal foreground, tank-dominant exterior background, no wide launch spectacle.`
- `allowed_anomaly_carriers`: `human warning posture, terminal attention, isolated upper-tower placement`
- `banned_anomaly_carriers`: `readable terminal text, NASA logos, heroic astronaut pose, office boardroom, explosion, takeoff, extra people crowding the frame`
- `text_logo_ui_risks`: `Terminal screens and badges can leak text or NASA marks; keep screens as unreadable glow and crop uniforms/logos away.`
- `deformation_or_model_risks`: `Human hands, terminal controls, tower geometry, and tank/shuttle proportions can deform; use simple blocking and avoid complex hand detail.`
- `still_prompt_hypothesis`: `Upper launch-tower side terminal with one engineer proxy frozen in warning posture, orange external tank filling the exterior background, cold blue-gray steel, restrained documentary-surreal stillness.`
- `motion_risk_note`: `Motion should be minimal; preserve the figure scale and tank background. Do not let the human walk, sit, point, or create new furniture.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

### `beat_01b`

- `cue_range`: `00:00:06.719-00:00:11.185`
- `narration_excerpt_or_transcript_range`: `[00:00:06.719-00:00:11.185] They launched anyway, and the reason is more disturbing than the explosion itself.`
- `mechanism_claim`: `The launch context advances despite the warning; the wrong state is institutional momentum, not liftoff action.`
- `primary_subject`: `cold Challenger launch site in blue haze`
- `canonical_subject_constraints`: `Challenger must remain fixed on the pad with recognizable shuttle/tower silhouette and cold prelaunch atmosphere.`
- `historical_or_domain_reference_notes`: `Use pad, gantry, frost, and blue-haze references; this is the active Apple-native LTX exception beat only after reviewed keep proof.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/ice_on_pad_gantry/selects/ice_on_pad_gantry.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/launch_stack_exterior/selects/launch_stack_exterior.png; source IDs act3_06, act3_07, act3_08, act3_01`
- `palette_material_constraints`: `Frosted blue haze, cool gray tower, quiet tank orange, no fiery launch palette.`
- `camera_logic`: `Locked wide or medium-wide pad view; shuttle/tower silhouette fixed, no ascent or smoke plume.`
- `allowed_anomaly_carriers`: `temperature, haze density, subtle tower/service light cadence`
- `banned_anomaly_carriers`: `birds, ignition, takeoff, explosion, crowd, poster skyline, readable countdown text`
- `text_logo_ui_risks`: `Countdown clocks and pad signage can leak text; omit readable instrumentation.`
- `deformation_or_model_risks`: `Shuttle/tower geometry may melt under motion; preserve a locked camera and low motion amplitude.`
- `still_prompt_hypothesis`: `Cold Challenger launch pad held in blue haze, shuttle fixed in gantry, restrained prelaunch stillness with tower lights as the only pressure cue.`
- `motion_risk_note`: `Allow only light/haze pulses. No camera push, no birds, no ignition, no shuttle motion.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

### `beat_02a`

- `cue_range`: `00:00:12.188-00:00:16.053`
- `narration_excerpt_or_transcript_range`: `[00:00:12.188-00:00:16.053] The booster O-rings had shown erosion and blow-by before.`
- `mechanism_claim`: `The damage signal was already present in the hardware record. The frame must show a localized joint/O-ring warning without jumping to catastrophic failure.`
- `primary_subject`: `field-joint ring and O-ring seat in close documentary crop`
- `canonical_subject_constraints`: `The joint must read as cylindrical booster hardware with a ring interface, gasket seat, seam, and residue line.`
- `historical_or_domain_reference_notes`: `Use booster-joint evidence and recovered-debris references as mechanical constraints; this is an evidence insert, not a symbolic diagram.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/booster_joint_evidence/selects/booster_joint_evidence.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/recovered_booster_debris/selects/recovered_booster_debris.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/subject_reference_plates/generated/challenger_seal_joint.png`
- `palette_material_constraints`: `Off-white insulation, dark rubber seam, scorched gray residue, restrained archival lighting.`
- `camera_logic`: `Tight macro/documentary crop at the joint interface so the seam and blow-by evidence stay legible at Shorts scale.`
- `allowed_anomaly_carriers`: `localized dark seam, faint residue line, slight material mismatch at the interface`
- `banned_anomaly_carriers`: `wide shuttle, flame plume, exploding hardware, labels, arrows, cutaway text, exaggerated rupture`
- `text_logo_ui_risks`: `Technical diagrams and labels are tempting but banned; keep all evidence visual and wordless.`
- `deformation_or_model_risks`: `Circular hardware can warp into abstract bands; require coherent cylindrical geometry and a single seam.`
- `still_prompt_hypothesis`: `Close documentary crop of a booster field-joint ring and O-ring seat with one localized dark seam and faint residue line, quiet evidence lighting.`
- `motion_risk_note`: `Motion should preserve the seam and ring geometry; no spreading flame or widening context.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

### `beat_02b`

- `cue_range`: `00:00:17.074-00:00:24.925`
- `narration_excerpt_or_transcript_range`: `[00:00:17.074-00:00:24.925] Each flight that survived made the warning look more normal. Management had started treating the damage as acceptable.`
- `mechanism_claim`: `Repeated survival normalized damage; this beat should feel calm, procedural, and falsely acceptable.`
- `primary_subject`: `calm mid-stack Challenger launch-pad context frame`
- `canonical_subject_constraints`: `Shuttle stack/tank context must remain recognizable, centered enough for continuity after the O-ring insert, and free of visible disaster cues.`
- `historical_or_domain_reference_notes`: `Use shuttle stack and systems-overview references as continuity context after the hardware close-up.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/launch_stack_exterior/selects/launch_stack_exterior.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/shuttle_systems_overview/selects/shuttle_systems_overview.png; source IDs act2_01, act2_05, act2_06, act2_02`
- `palette_material_constraints`: `Muted tank orange, white shuttle surfaces, gray pad structure, low-contrast institutional calm.`
- `camera_logic`: `Medium stack context frame after close-up; calm continuation rather than new anomaly.`
- `allowed_anomaly_carriers`: `none; this is a continuity beat where calmness is the wrong state`
- `banned_anomaly_carriers`: `new flame, smoke, countdown text, diagram overlay, exaggerated surreal object`
- `text_logo_ui_risks`: `Avoid visible labels on shuttle or signs.`
- `deformation_or_model_risks`: `Mid-stack geometry can become toy-like or generic rocket; keep shuttle/tank/booster proportions simple and canonical.`
- `still_prompt_hypothesis`: `Calm mid-stack Challenger launch-pad context frame after the hardware warning insert, restrained and falsely routine.`
- `motion_risk_note`: `Use selected distilled canonical primary winner; no drift toward launch or disaster.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

### `beat_03`

- `cue_range`: `00:00:25.359-00:00:32.569`
- `narration_excerpt_or_transcript_range`: `[00:00:25.359-00:00:32.569] On January 27, NASA did not ask Thiokol to prove launch was safe. It asked them to prove it was unsafe.`
- `mechanism_claim`: `The burden of proof flips inside an institutional decision room.`
- `primary_subject`: `launch-decision table with authority imbalance, no table phone, and only faint whiteboard residue kept secondary`
- `canonical_subject_constraints`: `Room must read as a late-1980s engineering/management meeting space with table, folders, muted technical wall residue, and unequal posture across the table.`
- `historical_or_domain_reference_notes`: `Use Rogers Commission and control-room/interior references for institutional texture; do not render a generic courtroom or modern conference room.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/rogers_commission_room/selects/rogers_commission_room.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/monitoring_labor_bank/selects/monitoring_labor_bank.png; source IDs act3_01, act3_02, act3_03, act3_04`
- `palette_material_constraints`: `Fluorescent beige-gray room, dark table, paper off-whites, restrained institutional color; avoid warm courtroom drama.`
- `camera_logic`: `Locked room/tableau view across the table; posture and spacing carry the proof-burden reversal.`
- `allowed_anomaly_carriers`: `authority imbalance, empty chair pressure, one side physically compressed by table geometry`
- `banned_anomaly_carriers`: `readable whiteboard text, phones as focal props, modern laptops, courtroom iconography, pointing hands, shouting expressions`
- `text_logo_ui_risks`: `Whiteboard markings must be wordless residue only; no readable equations or labels.`
- `deformation_or_model_risks`: `Human/tableau beats risk extra limbs, sit/stand action, and furniture hallucination; use fixed positions and simple roles.`
- `still_prompt_hypothesis`: `Late-1980s launch-decision table, authority imbalance across the room, warning burden visually pushed onto one side, faint wordless whiteboard residue.`
- `motion_risk_note`: `Use recovered text-clean motion keeper; keep people fixed and avoid sit/stand or new props.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

### `beat_04a`

- `cue_range`: `00:00:33.631-00:00:36.975`
- `narration_excerpt_or_transcript_range`: `[00:00:33.631-00:00:36.975] At ignition, smoke appeared from the right booster joint.`
- `mechanism_claim`: `The hidden joint warning becomes visible at ignition, still localized and pre-catastrophic.`
- `primary_subject`: `accepted Challenger field-joint close-up family reused as the beat_04a still`
- `canonical_subject_constraints`: `Same joint family as beat_02a, now with a thin pale smoke/seep cue emerging from the interface.`
- `historical_or_domain_reference_notes`: `Constrain to booster-joint and smoke evidence; do not widen to the full launch stack.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/booster_joint_evidence/selects/booster_joint_evidence.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/breach_plume_tracking/selects/breach_plume_tracking.png`
- `palette_material_constraints`: `Cold off-white hardware, thin pale smoke, dark seam, no orange flame.`
- `camera_logic`: `Locked close crop at the joint interface; smoke/seep must be visible without becoming a plume.`
- `allowed_anomaly_carriers`: `one thin pale seam seep, localized smoke from the joint interface`
- `banned_anomaly_carriers`: `flame, wide shuttle view, explosion, ruptured booster, readable evidence labels`
- `text_logo_ui_risks`: `No labels or arrows; no technical diagram text.`
- `deformation_or_model_risks`: `Smoke can become flame or abstract mist; joint ring can warp under motion.`
- `still_prompt_hypothesis`: `Booster field-joint close-up with one thin pale seam seep emerging from the joint interface, no flame, no widened launch view.`
- `motion_risk_note`: `Use selected distilled canonical primary winner; reject widened-context drift.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

### `beat_04b`

- `cue_range`: `00:00:37.936-00:00:41.942`
- `narration_excerpt_or_transcript_range`: `[00:00:37.936-00:00:41.942] Around 58 to 59 seconds, flame became visible again.`
- `mechanism_claim`: `The failure signal reappears in flight while the vehicle is still intact.`
- `primary_subject`: `Space Shuttle Challenger airborne high above Earth in a restrained exterior documentary frame`
- `canonical_subject_constraints`: `The orbiter, external tank, and boosters must remain recognizable as Challenger in flight; Earth/sky context is secondary.`
- `historical_or_domain_reference_notes`: `Use shuttle flight and breach-plume tracking references; the frame must stay before breakup.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/breach_plume_tracking/selects/breach_plume_tracking.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/launch_stack_exterior/selects/launch_stack_exterior.png`
- `palette_material_constraints`: `High-altitude blue/black, white shuttle/tank read, small orange-white flame cue restrained to right booster joint path.`
- `camera_logic`: `Exterior telephoto-like vertical frame; vehicle remains intact, flame is visible but not dominant.`
- `allowed_anomaly_carriers`: `small flame along right booster joint path, restrained breach cue`
- `banned_anomaly_carriers`: `full explosion, breakup geometry, extra aircraft, dramatic fireball, UI tracking boxes, labels`
- `text_logo_ui_risks`: `No telemetry, tracking overlays, captions, or NASA marks.`
- `deformation_or_model_risks`: `Shuttle anatomy can fail in generated attempts; preserve reviewed locked-hold clip when generated candidates drift.`
- `still_prompt_hypothesis`: `Airborne Challenger exterior frame, vehicle intact, small flame visible again along right booster joint path, restrained documentary framing.`
- `motion_risk_note`: `Retain reviewed locked-hold keep clip; do not replace unless a generated candidate beats anatomy and chronology.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

### `beat_04c`

- `cue_range`: `00:00:42.802-00:00:47.548`
- `narration_excerpt_or_transcript_range`: `[00:00:42.802-00:00:47.548] At 73 seconds, Challenger broke apart. Seven people died.`
- `mechanism_claim`: `The accumulated normalization reaches catastrophic outcome; use historical exterior evidence rather than generated spectacle.`
- `primary_subject`: `actual exterior Challenger breakup event in open sky above Earth`
- `canonical_subject_constraints`: `Use historically recognizable breakup geometry and breach plume branching from the NASA 86-HC-220 crop.`
- `historical_or_domain_reference_notes`: `This beat is evidence-led. Generated breakup attempts stay diagnostic-only unless they preserve the historical geometry.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/shorts/challenger_short_minimal_surreal_v3_trimmed/still_overrides/beat_04c__nasa_86HC220_crop.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/breach_plume_tracking/selects/breach_plume_tracking.png`
- `palette_material_constraints`: `Archival sky blue, white smoke/plume branching, no stylized fireball palette.`
- `camera_logic`: `Portrait crop of the actual exterior breakup; preserve readable plume geometry and open sky scale.`
- `allowed_anomaly_carriers`: `historical breakup geometry, breach plume branching`
- `banned_anomaly_carriers`: `invented fireball, abstract smoke flower, debris rain, text overlays, memorial typography`
- `text_logo_ui_risks`: `No archival caption, border, timestamp, or source label should be baked in.`
- `deformation_or_model_risks`: `Generated versions can invent impossible shuttle fragments; prefer exact crop as source carrier.`
- `still_prompt_hypothesis`: `Use the portrait crop derived from NASA image 86-HC-220 as the beat_04c carrier; do not generate a replacement without explicit review.`
- `motion_risk_note`: `Use reviewed keep locked-hold clip on the exact NASA crop.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

### `beat_05`

- `cue_range`: `00:00:48.409-00:00:57.307`
- `narration_excerpt_or_transcript_range`: `[00:00:48.409-00:00:57.307] This was not one bad call. It was a system that learned to look at damage and call it normal. Small causes, massive consequences.`
- `mechanism_claim`: `The final thesis is organizational learning in the wrong direction: damage becomes normal operations.`
- `primary_subject`: `control-room thesis frame with indicator-block status wall`
- `canonical_subject_constraints`: `Control-room or status-wall environment must read as institutional monitoring logic, not a generic office or cockpit.`
- `historical_or_domain_reference_notes`: `Use routine console and monitoring-labor references; the status wall is abstracted but must remain wordless.`
- `reference_source_paths_or_urls`: `/Users/mike/Viz_CascadeEffects/references/episodes/challenger/routine_console_wide/selects/routine_console_wide.png; /Users/mike/Viz_CascadeEffects/references/episodes/challenger/monitoring_labor_bank/selects/monitoring_labor_bank.png; source IDs act2_03, act2_08, act3_01, act4_02`
- `palette_material_constraints`: `Dim gray-green control-room glow, off-white indicator blocks, subdued blue/gray institutional palette.`
- `camera_logic`: `Locked interior thesis frame; status wall dominates as a normalizing machine while people remain absent or incidental.`
- `allowed_anomaly_carriers`: `indicator blocks absorbing warning state into routine pattern, calm control-room symmetry`
- `banned_anomaly_carriers`: `readable warning labels, red alert UI, meme text, dramatic explosion on screens, logo walls`
- `text_logo_ui_risks`: `Status panels can become readable UI; keep all blocks abstract and wordless.`
- `deformation_or_model_risks`: `Rows of indicators can turn into text; enforce blocks, lights, and panels only.`
- `still_prompt_hypothesis`: `Control-room thesis frame with wordless indicator-block status wall, warning logic absorbed into normal operations, restrained institutional glow.`
- `motion_risk_note`: `Use selected distilled canonical primary winner; keep indicator pattern stable and text-free.`
- `open_visual_questions`: `none`
- `research_disposition`: `keep`

## Handoff

- `may_enter_stills_contact_sheet`: `true`
- `selected_research_gaps`: `none`
- `next_action`: `Use this packet with source_preserving_documentary_v1 and subject_render_matrix before still prompt drafting.`
