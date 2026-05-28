---
name: "cascade_effects_series_bible_v1"
description: "Plan, evaluate, package, or revise Cascade Effects episode strategy against the canonical full episode table and first-eight doctrine, producing alignment reads, episode briefs, slate recommendations, or greenlight verdicts."
---

# Cascade Effects Series Bible v1

Use this skill when planning, evaluating, packaging, or revising Cascade Effects episode strategy, season order, title/thumbnail direction, research greenlights, or long-form editorial briefs against the canonical full episode table and first-eight series bible.

Do not use this skill for active Shorts production, audio generation, still or motion judgment, production manifest approval, or fact-check signoff. Route active Shorts production to [/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md](/Users/mike/CascadeEffects/ops/agents/skills/youtube_shorts_production_v1/SKILL.md).

## Outcome Contract

This skill produces one or more of:

- a series-bible alignment read
- a season-order or slate recommendation
- a mechanism-led episode strategy brief
- a title and thumbnail strategy package
- a research greenlight verdict
- a rewrite note that brings an outline, script, or package back into Cascade Effects doctrine

This skill does not produce a finished sourced script, fact-check signoff, approved production manifest, asset promotion decision, or generic disaster recap.

## Required Source

Use [references/cascade_effects_full_episode_table_1_186.md](references/cascade_effects_full_episode_table_1_186.md) as the canonical source of truth for episode inventory and order.

Use [references/first_8_series_bible.md](references/first_8_series_bible.md) as the strategic source of truth for first-eight doctrine, waves, research filter, tone, and packaging rules. Its order must remain aligned to the canonical table.

When local episode configs, production docs, or channel materials disagree with the canonical table or first-eight doctrine, flag the mismatch before recommending edits. Do not silently rewrite slate labels, manifests, or production state.

## Core Doctrine

Cascade Effects is a forensic, evidence-first documentary channel about how systems stop noticing what has changed until consequences make the change visible.

Every episode should answer:

> What shifted, who failed to recognize the shift, and how did the system convert that blindness into consequence?

The audience promise is:

> You already know the headline. We will show you the mechanism.

For long-form receipts/legend episodes where source evidence narrows a familiar public story, use `long_form_receipts_legend_signoff_v1` as the repeatable terminal VO sign-off:

> The legend fades. The receipts remain.

Do not use the audience-promise wording as a final sign-off; it is a positioning promise, not the terminal cadence.

The first-eight throughline is:

> Every episode is about a system that stopped noticing what had changed.

## Decision Logic

First classify the request:

- `alignment`: critique an outline, script, package, slate, title, or thumbnail against the bible
- `episode brief`: create or revise a mechanism-led strategy brief
- `slate`: recommend order, waves, episode roles, or launch sequencing
- `packaging`: shape title and thumbnail direction
- `greenlight`: evaluate a future topic against the six research dimensions

Then name the hidden mechanism before recommending structure, title, thumbnail, or release timing. If the mechanism is unclear, make that the blocker.

Classify each episode or candidate into one primary lane:

- `Design Failures That Changed the World`: What constraint failed, and how did the system let it fail?
- `One Decision Changed Everything`: When did the available options narrow, and who narrowed them?
- `Mystery That Has Receipts`: What does the record say that the legend leaves out?

Use secondary lanes only when they clarify packaging or audience expectation.

## Episode Strategy Rules

Use the 10-part long-form spine from the reference file unless the user explicitly asks for an experiment, but keep the script compact enough to avoid circular, repetitive, or over-philosophical narration.

The effective Season 2+ production target is compact long-form: default to 12 to 18 minutes, allow up to about 20 minutes when the source record genuinely needs it, and do not plan or draft toward 24 to 32 minutes unless Mike explicitly approves a special expanded episode. The older 24 to 32 minute target is superseded for active production planning because Season 1 production settled around a 16:42 average and later episode gates used 12 to 15 minute compact targets.

Build from changed-first framing: start with what changed inside the system, what made that change hard to see, and how delayed recognition became consequence.

Separate evidence from interpretation. Use primary and credible secondary sources for factual claims; mark missing proof as a research need rather than smoothing over the gap.

## Packaging Rules

Package the familiar surface and deliver the hidden mechanism.

Titles should combine the known subject, the hidden mechanism, and the sense that the public story is incomplete. Avoid generic `explained` framing, scandal-bait, conspiracy, or villain-first packaging.

Thumbnails should use one object or artifact, one hidden mechanism, one visual question, and 2 to 4 words maximum. Keep documentary seriousness; no YouTube-face theatrics, and no red circles unless they reveal a real mechanism.

## Output Shapes

For `alignment`, return `Verdict`, `Mechanism`, `Alignment`, `Drift Risks`, and `Recommended Changes`.

For `episode brief`, return `Episode`, `Primary Lane`, `Mechanism`, `Public Version`, `Incomplete Version`, `Causal Layers`, `Point Of No Return`, `Compressed Thesis`, `Title Directions`, `Thumbnail Direction`, and `Research Needs`.

For `slate`, return `Recommended Order`, `Wave Logic`, `Episode Roles`, `Audience Training Effect`, `Repo Or Doc Mismatches`, and `Next Decisions`.

For `greenlight`, score the candidate against the six dimensions in the reference file and return `Decision`, `Qualifying Dimensions`, `Weak Dimensions`, `Mechanism Candidate`, `Packaging Candidate`, and `Research Or Visual Needs`.

## Hard Rules

- Do not tell the audience what happened first; tell them what changed first.
- Choose episodes where the evidence reveals a system, not just a story.
- Treat delayed recognition, not disaster, as the throughline.
- Do not reduce episodes to heroes, villains, trivia, or negligence-only hindsight.
- Do not greenlight a dramatic topic if the causal mechanism is not structurally legible.
- Do not present conjecture as receipts.

## Edge Cases

- If the user asks for Shorts production, use this skill only for strategy and then route production to the active Shorts skill.
- If the local repo has fewer or differently ordered episode configs than the canonical full episode table, flag that mismatch instead of treating either side as invisible.
- If a topic is famous but structurally weak, recommend deferral or a narrower mechanism.
- If a topic is obscure but has a strong evidence trail and visual mechanism, evaluate it seriously instead of rejecting it for low familiarity.
- If a story involves victims or institutional harm, keep the tone calm, precise, and emotionally controlled.
- If the user asks for titles before the mechanism is clear, give title directions only after naming the mechanism candidate.

## Example

User request:

> Does Titanic fit the first-eight slate, and how should we package it?

Expected response:

- `Decision`: greenlight as a prestige/scale episode if the lifeboat regulation gap remains the central mechanism.
- `Primary Lane`: Design Failures That Changed the World, with compliance-as-safety as the governing frame.
- `Mechanism`: compliance mistaken for safety after regulation lagged behind ship scale.
- `Season Role`: mass-recognition episode that tests whether the audience now trusts the channel method on a familiar story.
- `Packaging`: title directions such as `Titanic: Legal, Compliant, and Not Safe`; thumbnail anchored on lifeboats, capacity, or a regulation artifact.
- `Research Needs`: primary regulatory history, ship capacity/lifeboat numbers, contemporary safety assumptions, and a source-separated account of myth versus record.
