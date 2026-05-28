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
- Treat old Cascade Effects roots as external reference archives only. Current production must not read them directly; migration provenance belongs in `ops/migration/` and Season 1 audit material belongs in `archive/season-01-reference/`.
- Keep active episode work inside `episodes/season-02/`. Season 1 is reference-only inside this repo.

## Production Gates

- Route long-form episode strategy through `ops/agents/skills/cascade_effects_series_bible_v1/SKILL.md`.
- Route long-form audio/script production through `ops/agents/skills/episode_production_v1/SKILL.md`.
- Route long-form YouTube video production through `ops/agents/skills/long_form_video_production_v1/SKILL.md`.
- Route Shorts production through `ops/agents/skills/youtube_shorts_production_v1/SKILL.md`.
- Route Shorts final export through `ops/agents/skills/youtube_shorts_final_export_v1/SKILL.md`.
- Route publish readiness and review upload through `ops/agents/skills/youtube_shorts_publish_v1/SKILL.md` or the long-form publish workflow. Public release stays manual.
- Use `apps/review/` only through `bin/ce review-server`, `bin/ce review-list`, `bin/ce review-approve`, and `bin/ce review-reject`.

## Visual Rules

- Paper Architecture is allowed for CascadeEffects.tv website assets, channel-level branded assets, and website thumbnail-gallery images.
- Do not use Paper Architecture for long-form or Shorts source art, stills, keyframes, motion, proof frames, final frames, cover frames, chapter cards, effect maps, in-video end screens, or video thumbnails.
- For long-form source art, default to Codex ImageGen only in non-Paper style unless a human-approved exception names the episode, source paths, reason, risk, and affected outputs.

## Multi-Agent Rules

- Claim work with `bin/ce claim-task` before editing an active episode or shared workflow.
- Release work with `bin/ce release-task` when done or blocked.
- Keep task outputs inside the episode folder, `ops/`, or `.artifacts/` as specified by the task.
- Run `bin/ce doctor` before committing production workflow changes.
- Do not recreate top-level `agents/`, `audio/`, `viz/`, `inbox/`, `labs/`, `channel/`, or `episodes/season-01/`.
