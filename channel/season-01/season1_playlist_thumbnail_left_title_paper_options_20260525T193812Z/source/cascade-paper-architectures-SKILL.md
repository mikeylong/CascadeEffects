---
name: cascade-paper-architectures
description: Create Cascade Effects Paper Architecture briefs and prompts only for website surfaces, YouTube channel-branding assets, and CascadeEffects.tv website thumbnail-gallery images.
---

# Cascade Paper Architectures

Use this skill when creating or critiquing Cascade Effects Paper Architecture briefs, image-generation prompts, raster/source-art carrier plans, reference renders, homepage heroes, web section art, CascadeEffects.tv website episode-gallery thumbnails, YouTube channel banners, channel profile/icon derivatives, channel watermarks, or channel-level identity mockups.

Do not use this skill for video-production assets. YouTube Shorts, long-form video Living Covers, chapter cards, effect maps, in-video end screens, motion intros, proof frames, final frames, cover frames, and YouTube episode/video thumbnails are outside this skill unless Mike explicitly reclassifies the requested artifact as a website surface, a YouTube channel-branding surface, or a CascadeEffects.tv website thumbnail-gallery image.

## Operating Intent

Make Cascade Effects visuals repeatable and recognizable. The house style is `cascade-paper-architectures-ink-lit-v1`: ink-lit Paper Architectures built from deep ink-blue fields, cream folded paper forms, lavender paper shadows, dry cyan vellum signal traces, restrained coral warning accents, foam-core, vellum, gouache, and clean low-detail architectural models. The art should explain hidden systems without becoming gritty documentary, noir, smoke, plastic toy, literal water features, or generic low-poly debris.

This skill produces briefs and prompts. It does not generate images by itself unless the user separately asks for image generation.

## Scope Boundary

Paper Architecture is allowed only for:

- CascadeEffects.tv website heroes, section art, open-graph/brand surfaces, and related website visual assets.
- CascadeEffects.tv website episode-gallery thumbnail images.
- YouTube channel-level branded visual assets such as banners, profile-image derivatives, channel watermarks, and channel identity mockups.

Paper Architecture is not allowed for:

- YouTube Shorts visual assets, including stills, keyframes, motion, proof frames, final frames, cover frames, or in-video graphics.
- Long-form YouTube video assets, including Living Cover source art, backplates, chapter cards, cue/effect maps, rough proofs, final renders, cover frames, or in-video end screens.
- YouTube episode/video thumbnails that are packaged with a specific video rather than a website gallery card or channel-branding surface.
- Podcast covers, social posts, trailers, motion intros, or package assets unless Mike explicitly reclassifies them as one of the allowed website/channel-brand surfaces.

When a request targets a video asset, route to the active video workflow and use its non-Paper-Architecture visual style. Do not adapt Paper Architecture into a video style variant.

## Carrier Boundary

Paper Architectures is a raster/source-art visual direction, not a code-native illustration system.

- Public anchors, evidence objects, paper terraces, cascade sheets, architecture, vehicles, people, and scene backgrounds must be generated or approved as bitmap/source visual assets before they are used in a production proof.
- HTML, CSS, SVG, canvas, or other procedural code may provide only the wrapper: player shell, timing, captions, deterministic local typography, safe-zone layout, masks, transforms, and layer compositing over approved visual assets.
- Do not draw the core scene, subject, public anchor, evidence object, or Paper Architecture material system procedurally in CSS/SVG/canvas unless the user explicitly asks for a code-native diagnostic mockup.
- A code-native mockup is not a production visual proof, reference render, motion-readiness input, rough-assembly baseline, thumbnail, or package asset. Label it `diagnostic_only` and require a raster/source-art replacement before promotion.

## Surface Texture Boundary

Paper Architectures uses clean tactile paper, not noisy rendering.

- Allow subtle paper fibers only, scored seams, foam-core cut edges, soft pigment, vellum translucency, and material shadows.
- Ban high-frequency speckle, visible grain, grit, sandy paper surfaces, noisy texture, texture-heavy rendering, AI shimmer, and any surface texture that competes with the public anchor or evidence object.
- Prompts must include: `subtle paper fiber only, clean low-detail paper planes, no speckle/noise/grain/grit/sandy texture`.
- At `320x180` and `168x94`, the asset must read as clean paper planes. If texture dominates, reduces public-anchor clarity, or makes the evidence object harder to read, record `texture_noise_read: tighten` or `texture_noise_read: reject`.
- For clean-surface repair packets, also record `texture_detail_creep_read: pass|tighten|reject`. Texture is allowed only as minimal material tactility; visible paper grain, speckle, grit, sandy surface, fiber clumps, mottled background texture, AI shimmer, rough plaster, fabric-like weave, noisy shadows, over-detailed micro-surface, or texture competing with public-anchor readability is a blocker.
- Any allowed website, channel-branding, or website-gallery asset with `texture_noise_read: tighten` or `texture_noise_read: reject` cannot advance to `keep`, final package, or publication handoff until repaired and re-reviewed.

## Signal Trace Boundary

In Cascade Effects, `cascade` means cause-and-effect signal flow, not literal water.

- Express cyan motion/causality cues as a dry vellum signal trace, flat paper ribbon, small suspended signal markers, or a thin non-liquid glow.
- Ban water, waterfalls, rivers, streams, canals, liquid spills, flowing channels, watercourses, and any blue element that reads as liquid.
- Prompts for source art with cyan path cues must include: `dry cyan vellum signal trace, no water/waterfall/river/stream/canal/channel/liquid spill/glowing watercourse`.
- Any generated proof or source-art candidate where the cyan cue reads as water must record `waterfall_read: tighten` or `waterfall_read: reject`; only `waterfall_read: pass` can advance to `keep`, final package, or publication handoff for the allowed website, channel-branding, or website-gallery surface.
- For reference-anchored launch-pad and infrastructure scenes, dry signal traces must not become visible flags, tabs, ribbons, tape scraps, stickers, labels, UI markers, or colored tags on real-world hardware. Omit cyan/coral from the infrastructure, or confine any color to a tiny flush hairline inlay inside a separate evidence object; standalone coral/orange blocks, cubes, warning tabs, and random colored accent props are blockers.

## Visual System

Use these archetypes deliberately:

- **Evidence Terraces:** default grammar for allowed website and channel-branding assets. Stepped paper architecture with artifacts arranged like evidence, not debris.
- **Folded Cascade Model:** large-format brand world for homepage heroes, channel banners, and open graph images.
- **Human-Scale Paper System:** website/channel-branding variant only when a small observer clarifies scale. Do not use it for Shorts, trailers, or other video assets.

Material language:

- folded paper planes, scored seams, subtle visible paper fibers
- foam-core terrain and cut edges
- dry translucent vellum signal sheets and flat paper traces
- gouache and pastel pigment
- deep ink-blue fields, cream paper forms, lavender paper shadows, dry cyan vellum signal glow
- controlled museum-model lighting
- clean low-poly geometry with readable silhouettes

Hard avoid:

- dark documentary mood, noir lighting, gritty texture, smoke
- high-frequency speckle, grain, grit, sandy/noisy paper surfaces, texture-heavy rendering
- disaster spectacle, explosions, wreckage piles, dense debris
- water, waterfalls, rivers, streams, canals, liquid spills, flowing channels, glowing watercourses
- plastic toy gloss, mascot/kawaii styling, photorealism
- CSS/SVG/canvas/procedural approximations of the core illustration, flat icon systems, or placeholder art that only borrows the palette
- readable generated text, logos, captions, watermarks, labels, or title lettering unless deterministic local composition is explicitly requested
- bright/daylight Paper Architectures as the active default unless the asset is explicitly marked legacy/reference

## Recognizability Rule

Every visual brief needs a three-level object ladder:

1. **Public anchor:** an immediately recognizable subject silhouette or setting that does not require episode context.
2. **Evidence object:** the specific causal artifact, document, component, or record.
3. **System clue:** a supporting system object that reinforces cause-and-effect.

Exception: CascadeEffects.tv web episode-gallery thumbnails use a subject-dominant lane. For these small website cards, one dominant primary subject is the required read, and the surrounding card pill/title carries the case context. Do not add separate evidence trays, ledgers, gauges, connection details, terminal cards, system diagrams, arrows, dry signal paths, or secondary prop clusters unless the user explicitly asks for them and they cannot compete with subject recognition. Decorative cyan/coral tabs, flags, ribbons, markers, stickers, tape scraps, cubes, warning accents, or colored tags are blockers.

For small assets like thumbnails, the public anchor must dominate. Do not rely on an O-ring, ledger, lifeboat, trim wheel, or shop drawing alone unless the asset has surrounding context. For larger editorial assets, evidence objects can become more prominent, but a public anchor still needs to be visible.

For episode-specific source art, do not let the public anchor collapse into the channel homepage-hero grammar. Homepage folded mountain stages, folded terrain terraces, generic cascade waterfall/terrace heroes, title-bearing brand-hero artifacts, toy shuttles, toy evidence rings, and isolated subject-on-platform motifs are not acceptable substitutes for a reference-anchored scene. When the episode requires a real public setting, such as Challenger on the launch pad, scene fidelity comes first and Paper Architecture treatment comes second.

For Challenger launch-pad source art, scene fidelity also means plausible pad hardware. Record `brand_signal_artifact_read: pass|tighten|reject` and `pad_hardware_authenticity_read: pass|tighten|reject`; any non-pass value blocks advancement.

Read `references/artifact-recognition.md` when the asset is episode-specific or when object recognizability is uncertain.

## Asset Defaults

- **Homepage hero / channel banner:** Folded Cascade Model, wide ink-lit negative space, one dominant public anchor, evidence objects secondary. Approved title-bearing identity reference renders are allowed only when the package manifest names them.
- **CascadeEffects.tv web episode-gallery thumbnail:** Subject-only ink-lit Paper Architecture, one dominant primary subject, no generated text, no separate evidence/system props, no decorative cyan/coral artifacts. The web card pill/title carries context; preserve recognizability at `320x180` and `168x94`.
- **YouTube channel branding:** Paper Architecture may be used for channel banners, profile-image derivatives, video watermark/source marks, and channel identity mockups through the YouTube channel-branding workflow.
- **YouTube episode/video thumbnails:** out of scope for Paper Architecture by default. Use the active video/metadata packaging workflow unless Mike explicitly classifies the request as channel branding or a website gallery thumbnail.
- **Shorts / trailer / motion intro:** out of scope. Video assets do not use Paper Architecture.
- **Long-form living cover / chapter card / effect map:** out of scope. Video assets do not use Paper Architecture.
- **Podcast cover / square social:** out of scope unless Mike explicitly reclassifies the asset as a website/channel-branding surface.
- **Profile icon / favicon:** derived folded-paper `CE` or single cascade tile, not a full scene.
- **Web section art / newsletter:** Evidence Terraces with more negative space and lower artifact density.

Use `references/prompt-patterns.md` for compact templates by asset type.

## Workflow

1. Identify the asset type, format, channel, and whether title/text will be locally composed.
2. Declare the carrier: prompt-only brief, generated raster/source art, sourced raster/source art, hybrid raster/source art, or deterministic local composition over an approved raster/source baseline.
3. Choose one archetype from the visual system; default to Evidence Terraces when unsure.
4. Build the recognizability ladder before writing the prompt.
5. Keep the prompt ink-lit, tactile, material-specific, and explicit about subtle paper fiber only.
6. Include an avoid list that blocks bright/daylight defaults, noir, smoke, gritty documentary mood, water/waterfalls/rivers/streams/liquid channels, toy gloss, clutter, generated text, CSS/procedural placeholder art, and high-frequency speckle/noise/grain/grit/sandy texture.
7. Add QA notes for scale, cropping, title-safe zones, artifact legibility, carrier boundary, `texture_noise_read`, and `waterfall_read`.

If the user asks for actual images, use the image generation workflow after producing the brief. Keep project-bound images out of `.codex/generated_images` only if they are selected for use in the project and the user approves moving/copying them.

## Edge Cases

- If the episode is unknown, ask for the topic only if the asset cannot be made from the channel-level system; otherwise use a generic dry signal trace, paper trail, gauge, and warning-light ladder.
- If the requested artifact is too obscure at thumbnail scale, promote a public anchor and demote the artifact to secondary evidence.
- If the user asks for generated title text, prefer text-free source art plus deterministic local composition. Web/channel identity art may use approved title-bearing reference renders only when the package manifest explicitly permits them.
- If the user asks for an HTML player, proof page, motion prototype, Short, long-form video, or video thumbnail/cover frame, do not use Paper Architecture. Route to the active video workflow and its non-Paper-Architecture visual style.
- If a prior proof drew the public anchor, evidence object, or Paper Architecture scene with CSS/SVG/canvas, treat it as `diagnostic_only` unless the user explicitly approved code-native illustration as the goal.
- If an asset must crop across multiple channels, specify the safest public anchor placement first, then compose evidence objects around that crop.
- If a request conflicts with the allowed Paper Architecture surfaces, name the conflict and route to the correct workflow. Do not keep the prompt paper-built for video assets.

## Output Contract

Return:

- **Recommendation:** chosen archetype and why.
- **Asset Brief:** format, composition, material language, palette, title/text policy.
- **Carrier Plan:** prompt-only, generated raster/source art, sourced raster/source art, hybrid raster/source art, or deterministic composition over an approved raster/source baseline.
- **Recognizability Ladder:** public anchor, evidence object, system clue.
- **Prompt:** production-ready image-generation prompt.
- **Avoid List:** concise negatives.
- **QA Notes:** checks for scale, cropping, recognizability, brand fit, `texture_noise_read: pass|tighten|reject`, and `waterfall_read: pass|tighten|reject`.

For multiple assets, return one brief per asset and keep the shared visual rules once at the top.

## Compact Example

Request: "Create a Challenger thumbnail."

Output direction:

- Asset type: CascadeEffects.tv web episode-gallery thumbnail.
- Archetype: subject-only ink-lit Paper Architecture.
- Primary subject: space shuttle launch stack dominates the frame.
- Omit: O-rings, ledgers, checklists, gauges, arrows, system diagrams, signal paths, secondary prop clusters, decorative cyan/coral artifacts, generated text.
- Composition: clean launch stack built from cream folded paper and foam-core forms against deep ink-blue fields, lavender shadows, controlled museum-model lighting, dry model staging, text-free source art.
