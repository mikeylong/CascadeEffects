# DP Research And Constraint Policy

## Purpose

This policy implements the Challenger-first production restart. Visual production begins from a scoped Challenger short, and all prior visual constraints are inactive by default. The DP owns which constraints become active for the episode.

## Restart Rule

- Challenger is the only active restart target until a workflow scope manifest opens another episode.
- Existing visual constraints from Challenger, Hyatt, Therac, 737, keeper registries, casebooks, old manifests, old prompt packages, old renders, model experiments, and packaging rules are `legacy_reference` until reapproved in the current episode constraint ledger.
- The restart audit at [restart_constraint_audit_challenger_hyatt_therac_737.md](restart_constraint_audit_challenger_hyatt_therac_737.md) classifies current known episode/model/style constraints as legacy by default.
- No still or motion generation may start from inherited constraints alone.

## Required Order

1. Create a DP-approved `workflow_scope_manifest`.
2. Create a DP research brief from the scoped source/audio inputs and the narration map.
3. Produce visual research evidence within the scope and rank artifacts for downstream scene strength, mechanism visibility, and motion potential.
4. Derive the canonical visual beatmap from the strongest research artifacts.
5. Produce `shot_plan_v2` from the visual beatmap.
6. Convert research-backed decisions into a DP-approved episode constraint ledger.
7. Generate stills only from the active scope plus active ledger constraints.

## Scope Hydration

Agents may hydrate active context only from:

- `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/<new_challenger_short_id>/`
- `/Users/mike/CascadeEffects/archive/season-01-reference/original-episodes/Ep1_Challenger/shorts/<new_challenger_short_id>/production/`
- `/Users/mike/CascadeEffects/packages/media-pipeline/viz/references/episodes/challenger/shorts/<new_challenger_short_id>/`
- exact whitelisted source/audio files listed in the manifest
- exact DP-imported prior artifacts listed in the manifest

Blocked by default:

- `/archive/`, `/archives/`, `/experiments/`, `/legacy/`, `/retired/`, `/midjourney/`, `/proof_stills/`
- diagnostic outputs, mixed-review outputs, old renders, old manifests
- old casebook, keeper-derived, model-experiment, packaging, or previous-episode constraints

If an agent finds useful legacy material, it must stop and request a DP import. The DP import must list the exact path, reason, and allowed use.

## Constraint Ledger Rules

- The active ledger is the only source of visual constraints for the scoped short.
- Research may propose constraints, but the DP decides whether to activate, condition, retire, or keep them as legacy reference.
- A constraint must have evidence, scope, and owner before it can become `active`.
- Ledger changes reset visual research plus downstream visual stages for affected beats or shots.
- Old Challenger constraints do not outrank current research. Hyatt, Therac, and 737 constraints never apply to Challenger unless explicitly imported and activated.
- A narration map cannot activate visual constraints by itself. The research-driven visual beatmap is the canonical visual spine for stills and motion.

## Blocking Conditions

Block still generation when any of these are missing:

- DP-approved workflow scope manifest
- DP research brief
- visual research evidence packet
- research-driven visual beatmap
- `shot_plan_v2`
- DP-approved episode constraint ledger with `ledger_status: active`
- scoped active roots for the new Challenger short

Block context use when a source path is outside scope and has no exact DP import record.
