# YouTube Shorts Production Skill

## Policy References

- [Stage gate, promotion, and reset policy](references/stage_gate_policy.md)
- [Motion backend and dual-model matrix policy](references/motion_backend_policy.md)
- [Source-derived archival reanimation policy](references/source_derived_archival_reanimation_policy.md)
- [Historical signal texture profile registry](/Users/mike/Viz_CascadeEffects/references/style_packages/source_preserving_documentary_v1/archival_signal_texture_recipes.json)
- [Caption, text, and final-export handoff policy](references/caption_and_final_export_policy.md)
- [DP research and constraint policy](/Users/mike/Agents_CascadeEffects/references/skills/director_of_photography_v1/references/dp_research_constraint_policy.md)

## Source-First Motion Lane

When archival motion media provides the strongest visual language, do not default to Flux still generation. Use visual research to select clean source spans, source frames, and keyframe pairs, then route motion through one of:

- `direct_source_clip`
- `source_derived_reanimation`
- `still_driven_i2v`

`source_derived_reanimation` is the preferred middle lane when the source footage is visually right but the edit needs a different duration, cadence, or beat emphasis. It requires same-camera source keyframes, a no-audio normalized motion output, dense frame audit, and archival-fidelity review.

## House CRT Signal Texture

When an approved motion proof enters `video final`, the pipeline applies the Challenger-calibrated full-bleed CRT signal treatment as the first final-export substep, before captions or audio mux. This is a cross-episode house style, not an era-specific archival footage texture. Use `era_1980s_broadcast_crt_v1` at `visible_but_premium` for story clips, regardless of episode period/source medium, unless the coordinator records an explicit waiver.

Texture outputs must remain no-audio and full-bleed, with no TV frame, matte, border, rounded mask, or reduced image area. The final-export manifest must record the house CRT/signal-interruption manifest before a captioned final can advance. Challenger-style randomized signal interruption belongs only at eligible story-clip cuts as a mutation of outgoing footage, not as full-frame static cards.

## Challenger Restart Visual Gate

Do not generate a visual research packet for old `challenger_short_v1`, `challenger_short_v2_exact`, `challenger_short_v3_trimmed`, or prior restart folders. Challenger production restarts from a new scoped short root.

Before visual research or still generation, require:

- DP-approved workflow scope manifest
- DP research brief
- scoped visual research evidence
- DP-approved active episode constraint ledger

Visual research is incomplete unless each beat or shot has a recognizable source anchor, source paths or URLs, an anchor-preservation rule, and either an approved carrier mode or an explicit DP-approved non-literal exception.

All prior episode constraints, casebook lessons, keeper registry entries, old manifests, old renders, and model experiments are legacy by default. Use only scoped files and exact DP-approved imports.
