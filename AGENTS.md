# Agent Instructions

<!-- agent-memory-mcp:start -->
## Agent Memory Policy

Use the `agent-memory` MCP server tools on every conversation turn.

1. Before drafting a response, call `memory_get_context` with the user's latest message as `query`, this workspace path as `project_path`, `max_items: 12`, and `token_budget: 1200` unless the task needs more context.
2. Use the retrieved memory context when reasoning and responding.
3. After drafting the response, call `memory_capture` with project scope for this workspace and a summary hint focused on durable preferences, constraints, decisions, owners, deadlines, paths, and repo facts.
4. For explicit durable facts, call `memory_upsert` in global scope for user-wide preferences or project scope with `metadata.project_path`.
<!-- agent-memory-mcp:end -->

## Workspace Contract

- Treat `/Users/mike/CascadeEffects` as the Cascade Effects production root.
- Use `cascade.toml` and `bin/ce` before inventing paths or workflow state.
- Keep this as a true monorepo: do not create nested `.git` repos or submodules.
- Do not write generated media into Git-tracked paths. Use `.artifacts/` and update the relevant `artifacts.lock.json`.
- Preserve old `/Users/mike/*_CascadeEffects` roots as read-only sources until the staged symlink cutover is explicitly performed.

## Production Gates

- Route long-form episode strategy through `agents/references/skills/cascade_effects_series_bible_v1/SKILL.md`.
- Route long-form audio/script production through `agents/references/skills/episode_production_v1/SKILL.md`.
- Route long-form YouTube video production through `agents/references/skills/long_form_video_production_v1/SKILL.md`.
- Route Shorts production through `agents/references/skills/youtube_shorts_production_v1/SKILL.md`.
- Route Shorts final export through `agents/references/skills/youtube_shorts_final_export_v1/SKILL.md`.
- Route publish readiness and review upload through `agents/references/skills/youtube_shorts_publish_v1/SKILL.md` or the long-form publish workflow. Public release stays manual.
- Use `inbox/` as the mandatory human approval surface for Season 2 gate decisions.

## Visual Rules

- Paper Architecture is allowed for CascadeEffects.tv website assets, channel-level branded assets, and website thumbnail-gallery images.
- Do not use Paper Architecture for long-form or Shorts source art, stills, keyframes, motion, proof frames, final frames, cover frames, chapter cards, effect maps, in-video end screens, or video thumbnails.
- For long-form source art, default to Codex ImageGen only in non-Paper style unless a human-approved exception names the episode, source paths, reason, risk, and affected outputs.

## Multi-Agent Rules

- Claim work with `bin/ce claim-task` before editing an active episode or shared workflow.
- Release work with `bin/ce release-task` when done or blocked.
- Keep task outputs inside the episode folder, `ops/`, or `.artifacts/` as specified by the task.
- Run `bin/ce doctor` before committing production workflow changes.
