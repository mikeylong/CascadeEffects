# Therac-25 Short Minimal Surreal v1 Midjourney Package

## Defaults
- Parameter suffix: `--v 7 --ar 9:16 --raw --s 75`
- Reference mode: `manual_upload_local_files_with_provenance`
- Curated `--no`: `text, watermark, logo, crowd, poster, explosion`
- Optional global style refs live in `lookrefs/` and are not part of the per-shot upload order.

## Source documents
- Style profile: `/Users/mike/Viz_CascadeEffects/workflows/style_profiles/minimal_surreal_editorial.json`
- Research notes: `/Users/mike/Viz_CascadeEffects/references/therac25_console_alarm/docs/sources.md`
- Transcript source of truth: `/Users/mike/Viz_CascadeEffects/tmp/transcripts_v3/therac_short_minimal_surreal_v1.diarized.srt`
- Board references remain available but are used selectively by shot: `/Users/mike/Viz_CascadeEffects/references/therac25_console_alarm/board/radiation_machine.jpg`, `/Users/mike/Viz_CascadeEffects/references/therac25_console_alarm/board/radiotherapie_device.jpg`
- Web-sourced references are varied by shot: `therac_varian_precision_linac.jpg`, `therac_varian_trubeam_room.jpg`, `therac_tel_hashomer_sbrt.jpg`, `therac_truebeam_close.jpg`, `therac_elekta_versa_hd_room.jpg`, `therac_radyoterapi_linac.jpg`, `therac_imrt_oropharyngeal_setup.jpg`
- Optional look refs from prior visual exploration: `lookrefs/01__therac_confidence_failure_draft_00012.png`, `lookrefs/02__therac_confidence_failure_final_00001.png`, `lookrefs/03__therac_impossible_repeat_final_00001.png`, `lookrefs/04__therac_device_head.png`, `lookrefs/05__therac_control_bank.png`

## Delivery Contract
- Midjourney is the source of truth for final stills on this lane.
- Drop approved Midjourney selects into `selects/` using the exact filenames listed below.
- After selects are in place, motion is rendered locally through the existing MLX `distilled` img2video path.

## Approved Still Drop Zone
- `selects/cover.png`
- `selects/beat_01.png`
- `selects/beat_02.png`
- `selects/beat_03.png`
- `selects/beat_04.png`
- `selects/beat_05.png`

## Optional Style Refs
- These are package-level look references for the current Therac minimal-surreal direction.
- They are not replacements for the per-shot upload orders listed below.
- If used in Midjourney, keep the shot-specific references first and treat the look refs as optional style guidance only.
- Preferred look refs: `lookrefs/01__therac_confidence_failure_draft_00012.png`, `lookrefs/03__therac_impossible_repeat_final_00001.png`, `lookrefs/04__therac_device_head.png`

## Cover
- Preset: `shorts_cover_plate/therac_confidence_failure`
- Prompt: Therac-25 reduced to one trusted radiotherapy device portrait carrying a hidden fatal flaw. single sealed machine head and housing dominate a quiet clinical field with no patient bed and no broad room overview. asymmetrical portrait framing weights the device left and preserves a wide negative field on the right, vertical 9:16. Palette stays bone white, pale cyan, charcoal, and a restrained internal warning red. one thin red fault seam glows from inside the otherwise calm device shell, implying failure hidden inside confidence. Soft frontal light, sealed surfaces, and a clinical quiet that never fully relaxes.
- References: cover/references/01__radiotherapie_device.jpg, cover/references/02__therac_truebeam_close.jpg, cover/references/03__therac_varian_precision_linac.jpg

## Shots
### beat_01
- Preset: `shorts_scene_plate/therac_impossible_repeat`
- Cue: 0.031s -> 7.043s
- Prompt: Therac-25 overdose, denial, then repeat shown as one treatment room caught after an impossible event has already happened twice. single machine and table geometry occupy an empty room with no operators, no patient, and no interface readout asked to explain the failure. composition leans off-center with the gantry and bed misaligned just enough to feel wrong, leaving unused floor and wall space around them in a vertical 9:16 frame. Palette stays clinical beige, off-white, muted teal, and a small phosphor-green cue. one duplicated beam-state trace appears twice through the machine head, making repetition itself the surreal breach. Diffuse ceiling light, suspended air, and a room that feels recently abandoned.
- References: beats/beat_01/references/01__radiation_machine.jpg, beats/beat_01/references/02__therac_varian_trubeam_room.jpg, beats/beat_01/references/03__therac_tel_hashomer_sbrt.jpg

### beat_02
- Preset: `shorts_scene_plate/therac_interlocks_removed`
- Cue: 7.964s -> 24.922s
- Prompt: Therac-25 after software replaced physical interlocks, leaving a treatment device able to fire at full power with the wrong state active. single gantry-head apparatus dominates the frame while the surrounding field is stripped back to pure clinical geometry instead of a generic room mood. framing favors the device head and its open working side, with harder asymmetry and less environmental context than beat_01, vertical 9:16. Palette shifts to off-white, pale cyan, charcoal, and a colder phosphor-green diagnostic glow. one missing-filter void and one state-mismatch line inside the head imply a race condition rather than an accident tableau. Cooler light, hard edges, and technical calm that hides the hazard.
- References: beats/beat_02/references/01__radiotherapie_device.jpg, beats/beat_02/references/02__therac_truebeam_close.jpg, beats/beat_02/references/03__therac_elekta_versa_hd_room.jpg

### beat_03
- Preset: `shorts_scene_plate/therac_first_overdose`
- Cue: 25.864s -> 35.774s
- Prompt: In 1985 a woman in Georgia was overdosed, died months later, and the room became evidence even while the machine was said to be incapable of that harm. single treatment table and machine anchor the scene as a clinical record image, with the room arranged like documentation rather than spectacle. composition pulls the table and beam path across the frame so the empty patient position is legible without depicting a body, vertical 9:16. Palette narrows to hospital beige, paper white, charcoal, and a restrained cauterized red. one directional injury trace cuts through the air between machine and table, reading as aftermath rather than action. Flat report light, sober stillness, and no sentimental drama.
- References: beats/beat_03/references/01__radiation_machine.jpg, beats/beat_03/references/02__therac_imrt_oropharyngeal_setup.jpg, beats/beat_03/references/03__therac_tel_hashomer_sbrt.jpg

### beat_04
- Preset: `shorts_scene_plate/therac_institutional_disbelief`
- Cue: 35.775s -> 43.898s
- Prompt: Operators kept using Therac-25, more patients were burned, and each self-investigation ended by declaring the system normal. single ready-state machine sits in an orderly treatment room that looks routine enough to pass a checklist. composition is steadier and more frontal than the earlier beats, emphasizing institutional normalcy and the false confidence of a machine left in service, vertical 9:16 frame. Palette stays pale beige, desaturated steel, charcoal, and a buried warning red. one warning trace is absorbed into the machine's ready-state geometry so the danger appears hidden inside normal operation. Institutional light, controlled surfaces, and an unnerving sense of official reassurance.
- References: beats/beat_04/references/01__therac_radyoterapi_linac.jpg, beats/beat_04/references/02__therac_varian_trubeam_room.jpg, beats/beat_04/references/03__therac_varian_precision_linac.jpg

### beat_05
- Preset: `shorts_scene_plate/therac_small_causes_massive_consequences`
- Cue: 44.881s -> 56.835s
- Prompt: Six people were catastrophically overdosed because no one designed for the possibility that the software was wrong. single trusted radiotherapy machine is isolated as a final thesis object, with severe negative space making the system's confidence feel larger than the room around it. composition pushes the device to one side and leaves the rest of the frame almost empty, turning scale and silence into the consequence, vertical 9:16. Palette reduces to off-white, pale cyan, charcoal, and one minute red breach. a hairline fault seam and faint red bleed are the only visible signs of the error that produced massive consequences. Low-contrast light, motionless air, and a final image that feels conclusive rather than dramatic.
- References: beats/beat_05/references/01__radiotherapie_device.jpg, beats/beat_05/references/02__therac_varian_precision_linac.jpg, beats/beat_05/references/03__therac_elekta_versa_hd_room.jpg
