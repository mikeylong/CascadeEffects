# CascadeEffects.tv Episode Gallery Thumbnail Workflow

Active website proof: `proof-v6-ink-lit-subjects`

This folder contains website episode-gallery thumbnail proofs. The website gallery is a subject-only lane, not the broader Paper Architecture evidence-ladder lane used for YouTube thumbnails, long-form covers, podcast art, or larger editorial assets.

## Active Rule

For CascadeEffects.tv episode-gallery cards, the image must focus on one dominant primary subject. The card pill and title carry the case context, so the thumbnail source art should not add separate evidence objects or system clues.

Use `cascade-paper-architectures-ink-lit-v1`:

- Deep ink-blue field.
- Cream folded-paper and foam-core forms.
- Lavender paper shadows.
- Controlled museum-model lighting.
- Crisp low-detail architectural construction.
- Subtle paper fiber only when nearly invisible.
- Text-free source art.

Do not add:

- Evidence trays, ledgers, gauges, connection details, terminal cards, system diagrams, arrows, dry signal paths, or secondary prop clusters.
- Decorative cyan or coral flags, tabs, ribbons, markers, stickers, tape scraps, cubes, warning accents, or colored tags.
- Water, waterfalls, rivers, streams, canals, liquid spills, glowing watercourses, smoke, explosions, wreckage spectacle, generated text, logos, labels, or watermarks.

## Proof History

- `proof-v3`: legacy approved composition logic. It established the one-subject website thumbnail read.
- `proof-v4-dark-adapted`: legacy/reference only. It was a dark adaptation of proof-v3, not fresh ink-lit source art.
- `proof-v5-ink-lit-regenerated`: rejected/non-promotable. It over-applied the three-level recognizability ladder and reintroduced evidence/system clutter.
- `proof-v6-ink-lit-subjects`: active reference. It is the current subject-only ink-lit baseline wired into `lib/site-facts.ts`.

Keep proof folders as provenance. Do not delete or overwrite legacy/rejected proofs.

## New Proof Folder

Use a fresh folder when replacing the active website baseline:

```text
brand/assets/episode-gallery/proof-vN-ink-lit-subjects/
brand/assets/episode-gallery/proof-vN-ink-lit-subjects/source-renders/
public/brand/episode-gallery/proof-vN-ink-lit-subjects/
output/episode-gallery/proof-vN-ink-lit-subjects/
```

Use the same slug and file pattern as proof-v6:

```text
{episode-id}-thumbnail-proof-vN-ink-lit-subjects-source.png
{episode-id}-thumbnail-proof-vN-ink-lit-subjects.webp
```

## Prompt Template

Start each prompt with the primary subject. Do not begin with evidence, system clues, or abstract causality.

```text
Render fresh Cascade Effects source art in cascade-paper-architectures-ink-lit-v1.

Subject: [one dominant primary subject], filling the frame as a clean website episode-gallery thumbnail. The image must remain recognizable at 320x180 and 168x94.

Style: deep ink-blue field, cream folded-paper and foam-core forms, lavender paper shadows, controlled museum-model lighting, crisp low-detail architectural construction, clean matte paper planes, subtle paper fiber only when nearly invisible.

Website gallery rule: subject-only composition. The card pill/title carries case context. Do not add separate evidence trays, ledgers, gauges, connection details, terminal cards, system diagrams, arrows, dry signal paths, or secondary prop clusters.

Accent rule: no decorative cyan/coral artifacts. Omit cyan/coral unless explicitly required by the approved subject itself; no tabs, ribbons, flags, markers, stickers, tape scraps, colored tags, cubes, or warning accents.

Hard bans: readable generated text, logos, labels, watermarks, photorealism, plastic toy gloss, noir/gritty mood, smoke, explosions, wreckage spectacle, water, waterfalls, rivers, streams, canals, liquid spills, glowing watercourses, visible paper grain, speckle, grit, sandy surface, fiber clumps, mottled background texture, AI shimmer, rough plaster, fabric-like weave, noisy shadows, or texture that competes with readability.
```

## Promotion QA

A website proof can be wired live only after:

- `texture_noise_read: pass`
- `texture_detail_creep_read: pass`
- `waterfall_read: pass`
- `brand_signal_artifact_read: pass`
- No generated text, logos, labels, or watermarks.
- Public subject remains readable at `320x180` and `168x94`.
- Runtime WebPs exist under `public/brand/episode-gallery/{proofId}/`.
- Source PNGs exist under `brand/assets/episode-gallery/{proofId}/source-renders/`.
- Provenance records status, prompt contract, selected source image paths, runtime paths, QA sheets, rejected-source exclusions, and the subject-only rule.
- Contact sheets exist at `320x180` and `168x94`.
- Homepage desktop and mobile screenshots show image loading, crop quality, card pill overlay, and no overlap.

Run before promotion:

```sh
npm run validate:episode-gallery
npm run validate:brand
npm run lint
npm run build
```
