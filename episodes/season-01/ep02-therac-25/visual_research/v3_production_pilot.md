# Therac-25 v3 Production Pilot

Legacy long-form R&D note. This document is not the active repo-level production workflow.

Active default workflow now lives at:

- `/Users/mike/Agents_CascadeEffects/references/skills/youtube_shorts_production_v1/SKILL.md`

## Purpose

This document turns Therac-25 from a broad visual-research lane into a production pilot using the minimal surreal v3 quality gates.

Source-of-truth workflow for this legacy long-form R&D note:

- still -> motion -> reel promotion: `/Users/mike/Viz_CascadeEffects/references/style_packages/minimal_surreal_editorial_v3/judgment/promotion_workflow.md`
- keeper registry: `/Users/mike/Viz_CascadeEffects/references/style_packages/minimal_surreal_editorial_v3/judgment/keeper_registry.md`
- proof note template: `/Users/mike/FluxLab_CascadeEffects/proofs/suites/_proof_review_template.md`

Production rule:

- FluxLab v3 stills are the source of truth for any frame that must animate.
- The old Midjourney short package remains useful as a concept/reference lane, not as the primary production lane for the long-form episode.

## Current Keeper Inventory

### Approved motion keepers

- `therac_25__operator_white_coat_cleanup`
  - still: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_therac_white_coat_cleanup/20260410T230153Z/therac_25__operator_white_coat_cleanup/minimal_surreal_editorial_v3/therac_25__operator_white_coat_cleanup__minimal_surreal_editorial_v3_00001_.png`
  - motion: `/Users/mike/AI/outputs/mlx-video/20260410T230813Z-765bd40b-comfy-therac_25__operator_white_coat_cleanup__minimal_surreal_editorial_v3_00001_-i2v-20260410T230828Z.mp4`
  - role: primary operator-behavior clip for the long-form pilot

- `therac_25__software_trusted_itself_pass_02`
  - still: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_therac_beat_10_software_trusted_itself_pass_02/20260411T052951Z/therac_25__software_trusted_itself_pass_02/minimal_surreal_editorial_v3/therac_25__software_trusted_itself_pass_02__minimal_surreal_editorial_v3_00001_.png`
  - motion: `/Users/mike/AI/outputs/mlx-video/20260411T054350Z-7d886bea-comfy-therac_25__software_trusted_itself_pass_02__minimal_surreal_editorial_v3_00001_-i2v-20260411T054350Z.mp4`
  - role: closing thesis motion lane

### Approved still keepers

- `therac_25__patient_vs_machine_pass_02`
  - still: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_therac_beat_01_patient_vs_machine_pass_02/20260411T054650Z/therac_25__patient_vs_machine_pass_02/minimal_surreal_editorial_v3/therac_25__patient_vs_machine_pass_02__minimal_surreal_editorial_v3_00001_.png`
  - role: opening contradiction still

- `therac_25__hidden_state_mismatch_redesign_pass_02`
  - still: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_therac_beat_04_hidden_state_mismatch_redesign_pass_02/20260411T054555Z/therac_25__hidden_state_mismatch_redesign_pass_02/minimal_surreal_editorial_v3/therac_25__hidden_state_mismatch_redesign_pass_02__minimal_surreal_editorial_v3_00001_.png`
  - role: supporting technical insert only; not the deferred Beat 04 hero frame

- `therac_25__trust_chain_machine_over_patient_pass_02`
  - still: `/Users/mike/AI/comfy/output/cascadeeffects_fluxlab/proofs/minimal_surreal_v3_therac_beat_07_trust_chain_machine_over_patient_pass_02/20260411T054555Z/therac_25__trust_chain_machine_over_patient_pass_02/minimal_surreal_editorial_v3/therac_25__trust_chain_machine_over_patient_pass_02__minimal_surreal_editorial_v3_00001_.png`
  - role: institutional trust bridge still

### Current rough cut

- rough cut: `/Users/mike/AI/outputs/mlx-video/20260411T061436Z-therac_v3_pilot_rough_cut_01.mp4`
- review note: `/Users/mike/FluxLab_CascadeEffects/proofs/suites/minimal_surreal_v3_therac_pilot_rough_cut_01.md`
- status: first keeper-only Therac pilot assembly exists

### Reference-only still package

- `/Users/mike/Viz_CascadeEffects/references/episodes/therac-25/shorts/midjourney/therac_short_minimal_surreal_v1/shot_list.md`

This package is useful for:

- removed-interlock still logic
- first-overdose room logic
- institutional-disbelief room logic
- thesis-object ending logic

Do not treat it as the approval source for motion-ready long-form frames.

## Production Constraints

- Use the locked script at `/Users/mike/Episodes_CascadeEffects/Ep2_Therac-25/Ep2_Therac-25.txt`.
- Use the locked audio master already on disk. Do not block planning on a missing mastered transcript.
- The episode TOML still points at a nonexistent mastered transcript path, so this pilot is anchored to script sections first and can be timecoded later.
- No beat may advance into motion unless its still review is `keep`.
- No assembly reel may be treated as a keeper reel unless every included clip is `keep`.

## Beat Spine

The pilot should use 10 long-form beats. Each beat has one primary image problem and one production strategy.

### Beat 01: Patient versus machine

- Script anchor: opening through `The hospital believes the machine.`
- Visual thesis: establish the split between bodily reality and machine certainty without sensationalizing the patient.
- Archetype: `room_or_interior`
- Primary subject: treatment room with Therac-25 and table
- Anomaly carrier: the room looks clinically normal while the beam-path relationship is wrong in one localized cue
- Production strategy: generate a new still
- Motion target: restrained room hold only if the still passes
- Notes: patient presence can be implied as a covered body form or table occupancy, but no pain tableau and no victim-forward framing

### Beat 02: The margin the machine is supposed to hold

- Script anchor: `Radiation therapy works...` through `The machine exists to hold that margin.`
- Visual thesis: make the apparatus of trust feel engineered, precise, and narrow
- Archetype: `single_object_or_device`
- Primary subject: radiotherapy head / beam-path apparatus
- Anomaly carrier: no anomaly yet; this beat establishes the promise of control
- Production strategy: generate a new still
- Motion target: still hold or slight parallax only
- Notes: this is a control beat; clarity matters more than surreal charge

### Beat 03: Hardware interlocks removed

- Script anchor: `The Therac-25 removed the hardware interlocks.` through `And the machine shipped.`
- Visual thesis: show the absent safety layer as the real event
- Archetype: `fragment_or_detail`
- Primary subject: beam-path hardware / missing interlock logic
- Anomaly carrier: one missing physical safeguard where a blocking mechanism should exist
- Production strategy: generate a new still, using the short-package interlocks-removed lane as a reference only
- Motion target: optional macro drift if the physical absence reads clearly
- Notes: keep this mechanical, not diagrammatic

### Beat 04: Hidden state mismatch

- Script anchor: `The Therac-25's software had a flaw...` through `there was nothing between the bug and the patient.`
- Visual thesis: procedural mismatch, not cinematic danger
- Archetype: `single_object_or_device`
- Primary subject: machine head / sealed housing / beam-state subsystem
- Anomaly carrier: one wrong-state cue in the head or beam path, with the machine body still trustworthy
- Production strategy: generate a new still
- Motion target: likely yes, if the mismatch stays localized and clean
- Notes: this is the core technical image problem of the episode

### Beat 05: Massive overdose, normal console

- Script anchor: `The overdose was massive...` through `The patient, or the machine.`
- Visual thesis: the contradiction between injury and normal reporting
- Archetype: `room_or_interior`
- Primary subject: treatment room with empty or recently vacated patient position
- Anomaly carrier: one concentrated injury trace or beam aftermath while the machine state remains calm
- Production strategy: generate a new still, using the short-package first-overdose room logic as a reference only
- Motion target: no motion until the still is unquestionably clean
- Notes: no body-forward suffering image; the room is the evidence

### Beat 06: MALFUNCTION 54 becomes routine

- Script anchor: `Sometimes a cryptic message appeared...` through `Through repetition.`
- Visual thesis: normalized override behavior is the mechanism of trust
- Archetype: `single_human_figure`
- Primary subject: operator at console
- Anomaly carrier: practiced hand workflow treating one warning state as ordinary
- Production strategy: reuse the approved keeper motion
- Motion target: already solved
- Notes: this is the first production beat that should enter the rough cut immediately

### Beat 07: Trust chain, machine over patient

- Script anchor: `Layer one: inherited reputation...` through `the data won.`
- Visual thesis: confidence accumulates structurally, not emotionally
- Archetype: `room_or_interior`
- Primary subject: orderly machine-in-room ready state
- Anomaly carrier: one hidden warning seam absorbed into normal machine geometry
- Production strategy: generate a new still, informed by the short-package institutional-disbelief lane
- Motion target: optional, only after a clean still exists
- Notes: avoid UI-led explanation; keep the machine trusted on first read

### Beat 08: Incidents repeat across hospitals

- Script anchor: `Between June 1985 and January 1987...` through `the pattern was there.`
- Visual thesis: repetition without central visibility
- Archetype: `room_or_interior`
- Primary subject: treatment room / machine / repeated beam-state aftermath
- Anomaly carrier: duplicated or repeated trace cue localized to one treatment configuration
- Production strategy: generate a new still
- Motion target: likely still hold rather than full motion
- Notes: this beat should feel procedural and distributed, not melodramatic

### Beat 09: Hager proves the machine can overdose

- Script anchor: `The investigation... Fritz Hager...` through `the case was closed.`
- Visual thesis: independent testing breaks the institutional frame
- Archetype: `fragment_or_detail`
- Primary subject: measuring hardware or test setup proving excessive output
- Anomaly carrier: one measured-output contradiction that cannot be ignored
- Production strategy: generate a new still
- Motion target: optional macro move if the measuring device remains canonical
- Notes: keep the shot about proof, not courtroom symbolism

### Beat 10: Final thesis, software trusted itself

- Script anchor: `Two causes...` through the closing lines
- Visual thesis: one calm machine portrait carrying the whole lesson
- Archetype: `single_object_or_device`
- Primary subject: Therac-25 as trusted thesis object
- Anomaly carrier: one hairline internal breach or wrong-state seam in an otherwise calm machine portrait
- Production strategy: generate a new still, informed by the short-package cover and beat_05 thesis-object logic
- Motion target: optional final hold if the still is strong enough
- Notes: this is the closing image, so it should be conclusive rather than explanatory

## Executed Production Queue

Executed in this order:

1. Beat 04 `hidden state mismatch`
2. Beat 06 `MALFUNCTION 54 becomes routine` using the existing keeper motion
3. Beat 03 `hardware interlocks removed`
4. Beat 05 `massive overdose, normal console`
5. Beat 10 `final thesis, software trusted itself`
6. Beat 07 `trust chain, machine over patient`

Current outcome:

- Beat 06 and Beat 10 are now approved Therac motion keepers.
- Beat 01 and Beat 07 are approved still keepers.
- Beat 04 is approved only as a supporting insert; the hero frame remains deferred.
- Beat 03 same-carrier macro strategy was exhausted and rejected.
- Beat 05 room-aftermath carrier remains useful conceptually, but its current framing family is exhausted and rejected due to arm-label leakage.

## Assembly Rules For The Pilot Cut

- Use `keep` motion clips directly.
- Use `keep` stills as held beats if motion is not yet approved.
- Use `diagnostic only` assets for internal comparison only, not in the pilot cut.
- Do not include Challenger/Hyatt cross-episode keeper clips in the Therac cut; they are benchmarks, not content.
- Treat this pilot as a rough-cut backbone, not a final full-coverage lock. The goal is to prove that one episode can move through the v3 gate system from stills to edit without falling back into abstract boards.

## Immediate Blockers

- The mastered transcript path in the episode TOML is stale and needs a refresh before precise cue timing can be locked.
- Beat 04 still lacks a separate hero frame. The approved insert is not the full technical-core solution.
- Beat 03 needs a different carrier, not another pass on the rejected safeguard-bracket macro.
- Beat 05 needs a different carrier or framing family if the overdose aftermath beat reopens.
- Beats 02, 08, and 09 still have no production stills in the current v3 lane.

## Done Means

This production pilot is ready for assembly when:

- at least 5 core beats have `keep` stills
- at least 2 Therac-specific beats have `keep` motion clips
- the opening, technical core, repetition, and closing thesis all have usable assets
- a Therac-only rough cut can be assembled without any diagnostic placeholders

Current state:

- `keep` still coverage exists for the opening, technical insert coverage, trust bridge, and both motion source stills.
- `keep` motion coverage exists for Beat 06 and Beat 10.
- a first Therac-only rough cut now exists without diagnostic placeholders, but Beat 04 hero coverage and the Beat 03/05 alternates remain deferred follow-ups.
