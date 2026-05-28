# Cascade Effects

One-page channel spec  
Version 1.0  
March 2026

## Repository canonical note

This file is the canonical written channel spec for this repository.

For styling decisions, `/Users/mike/CascadeEffects/apps/web/brand/cascade-effects-signal.style-system.json` is the canonical active source of truth and is validated against `/Users/mike/CascadeEffects/apps/web/brand/cascade-effects-signal.style-system.schema.json`.

The active visual profile is `cascade-lowpoly-pastel-v1`. Package asset rules are defined by:

- `/Users/mike/CascadeEffects/apps/web/brand/contracts/illustration.contract.json`
- `/Users/mike/CascadeEffects/apps/web/brand/contracts/design-system.contract.json`
- `/Users/mike/CascadeEffects/apps/web/brand/packages/*.package.json`

The token files treat brand colors and core packaging rules as exact. Font families, type scale, spacing, radii, shadows, layout, and motion are practical implementation defaults inferred to make the system usable immediately. When this document conflicts with the token files on visual implementation details, the brand folder takes precedence.

## Brand premise

Cascade Effects is a faceless documentary channel about hidden chains of cause and effect. Each episode shows how one decision, one flaw, one delay, or one ignored signal can reshape events far beyond the moment where it began.

## Core promise

Clear, evidence-led stories about decisions, failures, and hidden causes that changed the world.

## Positioning

Cascade Effects sits at the intersection of documentary storytelling, systems thinking, and historical investigation. It focuses on turning points, failure chains, and records that reveal what really drove an outcome.

## Audience

Curious viewers who want more than surface-level history. They care about systems, incentives, engineering, institutions, and the small details that produce large consequences.

## Content pillars

### 1. One Decision Changed Everything

Stories centered on a pivotal choice, delay, mistranslation, shortcut, or missed moment that altered the outcome.

### 2. Mystery That Has Receipts

Stories where paperwork, logs, records, manifests, transcripts, or official documents complicate the accepted version of events.

### 3. Design Failures That Changed the World

Stories about technical, organizational, or human-system failures, with emphasis on constraints, incentives, interface problems, and normalized risk.

## Editorial rules

- Start with a strong concrete hook.
- Follow the chain of cause and effect.
- Use evidence, not vibes.
- Keep the narration calm, clear, and serious.
- Prioritize clarity over drama.
- Avoid graphic framing, lazy shock tactics, and empty mystery bait.
- End with the key consequence or lesson.

## Brand voice

- Serious
- Clear
- Investigative
- Calm
- Precise
- Human, not theatrical

## Visual language

The visual system should feel like a bright cascade of small system failures becoming visible.

### Core look

- Bright pastel low-poly console-era 3D
- Clean faceted geometry
- Head-on cascade or waterfall motif
- Simple human operators, observers, analysts, or maintenance figures
- Large recognizable system-failure artifacts
- Minimal clutter
- Strong title hierarchy
- One dominant cascade surface, not stacked containers

### Color system

The repository token system uses a pastel low-poly palette anchored by:

- Deep ink: `#26324A`
- Cream surface: `#FFF8E8`
- Mint-cyan panel: `#BFECE8`
- Butter frame: `#FFF0B8`
- Lavender secondary shape: `#AFA6E8`

Accent color is motif-aware:

- Cascade/water accent: `#78DCE8`
- Failure/warning accent: `#FF6F61`

Usage rules:

- Use cyan for water/cascade energy and primary signal emphasis.
- Use coral only for warning lights, breakage, and small failure cues.
- Balance warm cream, butter, peach, and sand against cyan/mint/lavender so assets do not become one-note blue or purple.
- Do not use the old dark documentary base, neon signal-green accent, or archival collage grammar as active defaults.

### Typography

The repository token system uses:

- Primary sans family: Inter
- Technical and evidence family: IBM Plex Mono

Typography hierarchy should follow the token-defined editorial system:

- Wordmark, hero, thumbnail, section title, and card title treatments use a bold blocky sans hierarchy built on Inter.
- Evidence labels, metadata, technical callouts, and documentary annotations use IBM Plex Mono.
- Do not use the legacy draft headline font in repository implementations governed by the current brand folder.

### Layout and styling guardrails

- Panels, borders, radius, and shadow are allowed only as restrained implementation devices.
- Prefer one dominant surface, clear spacing, and dividers or rules over card stacks.
- Avoid boxes within boxes, nested card-on-card framing, decorative shadow stacks, and excessive rounded-corner treatment.
- Borders should read as editorial structure, not ornamental chrome.
- Shadows should separate a focal object or surface only when needed, not create a layered dashboard look.

## Thumbnail system

Use one rigid channel-level layout family across the channel.

- Title-only copy for launch package assets: `Cascade of Effects`
- Large deterministic title composed locally after source artwork generation
- Head-on cascade or waterfall as the primary image
- One to three human figures
- Six to eight large recognizable artifacts maximum
- Keep each thumbnail readable at small size
- Do not use clickbait faces or exaggerated emotional framing
- Avoid collage layouts, over-packed compositions, generated text, and photorealistic water

## On-screen style

- Clean captions
- Minimal animation
- Strong pacing
- Pastel low-poly scenes, simple overlays, maps, diagrams, documents, and archival stills over noisy montage
- Let the causal chain carry the scene
- Use motion sparingly and editorially; it should support reading and emphasis, not spectacle

## Channel tagline

Stories of decisions, failures, and hidden causes that changed the world.

## Channel description

Cascade Effects explores the hidden chains behind major events, design failures, and turning points in history. Each episode follows the decisions, constraints, incentives, and overlooked details that shaped what happened next. From engineering disasters to missed warnings to strange paper trails that contradict the legend, this channel looks past the headline and into the system behind it.

## Channel links

- Primary domain: https://cascadeeffects.tv
- Public contact: hello@cascadeeffects.tv

## Initial launch assets

- YouTube channel: Cascade Effects
- Handle: @CascadeEffects
- Profile image
- Banner
- Watermark
- One long-form thumbnail template
- One Shorts cover-frame template
- Tracking sheet for topics, pipeline, publishing, and performance

## Current launch direction

Lead with the first two recorded Design Failures episodes:

- Challenger
- Therac-25

Use them as anchor long-form episodes and cut multiple Shorts from each. Then expand quickly into one Decision episode and one Receipts episode to keep the channel broad enough to test all three pillars.

## Success criteria

The channel should feel:

- coherent
- evidence-led
- visually consistent
- easy to recognize
- repeatable to produce
- distinct from generic faceless history content
