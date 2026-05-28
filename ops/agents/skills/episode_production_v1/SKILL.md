---
name: "episode_production_v1"
description: "Inactive long-form production draft retained only to redirect current Cascade Effects production requests to active skills."
---

# Episode Production v1

Inactive draft. This earlier long-form-oriented production skill is no longer the active workflow.

Do not route current production work through this file.

Use the active Shorts production skill for active YouTube Shorts production:

- [/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md)

Use the series bible skill for episode strategy and slate decisions:

- [/Users/mike/CascadeEffects/ops/agents/skills/cascade_effects_series_bible_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/cascade_effects_series_bible_v1/SKILL.md)

## Contract

This inactive skill produces no current production artifacts. It returns only a routing note to an active skill.

This skill does not produce Shorts audio, stills contact sheets, stills video proofs, motion contact sheets, motion video proofs, video finals, caption overlays, or long-form rough cuts.

## Output Guidance

When selected accidentally, respond with:

- `status`: `inactive`
- `route_to`: active Shorts production skill or series bible skill
- `reason`: current production work must not use long-form rough-cut templates

## Near-Future Scope

- long-form audio podcast skill

## Far-Future Scope

- long-form video skill

## Edge Cases

- If a user asks for active Shorts work, route to the Shorts coordinator and preserve its gate sequence.
- If a user asks for long-form strategy, route to the series bible skill.
- If a user asks to revive long-form production, treat that as a new skill-design task rather than using these templates as active workflow.

## Example

Request:

> Build a Shorts final with captions.

Expected response:

- route to `/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md`
- do not use the inactive rough-cut templates in this package
