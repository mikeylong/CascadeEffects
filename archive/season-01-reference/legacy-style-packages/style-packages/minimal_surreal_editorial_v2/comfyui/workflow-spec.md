# ComfyUI / Flux Workflow Spec

## Graph layout

1. Load Checkpoint
   - Flux Dev or Flux Schnell for faster iteration
2. CLIP Text Encode (Positive)
3. CLIP Text Encode (Negative)
4. Empty Latent Image
5. KSampler
6. VAE Decode
7. Save Image

Optional nodes for stronger composition consistency:

8. Load Image
9. Image Resize / Crop
10. IPAdapter or composition reference node
11. Conditioning Combine

Optional batch exploration:

12. Repeat Latent Batch or increase batch size in latent node
13. Save filename prefix with seed embedded

## Recommended baseline settings for Flux

1. Model
   - Flux Dev for quality
   - Flux Schnell for rapid prompt tuning

2. Resolution
   - 1024 x 1024 for square exploration
   - 1024 x 1280 for portrait
   - 1024 x 1792 for 9:16 vertical sketches
   - 1536 x 864 for widescreen

3. Steps
   - 24 to 32

4. CFG / guidance
   - 3.5 to 5.5
   - Keep it moderate so the image does not overcook into unnecessary detail

5. Sampler
   - Use the Flux-recommended sampler in your build
   - If your setup exposes common samplers only, start with euler or dpmpp_2m

6. Seed strategy
   - Lock seed while tuning wording
   - Unlock seed for exploration once the prompt stabilizes

## Prompt discipline

- Prefer concrete nouns over abstract art-direction language.
- Prefer one clear scene state over stacked symbolic instructions.
- Do not encode caption-safe bands or keep-out rectangles into the model prompt.
- Do not force layout theory into every prompt.

## Prompt template

Use this structure every time:

[concrete subject + setting] + [what must remain recognizable] + [single anomaly or wrong state] + [palette logic] + [lighting/mood] + [restraint clause]

## Master prompt

restrained documentary-surreal image, one clear subject or scene, subject remains recognizable after simplification, reduced but not empty frame, controlled palette, one dominant anomaly or wrong state, stillness, clear silhouette, restrained detail, non-spectacular tension

## Negative prompt

text, watermark, logo, ui overlay, crowded scene, many small objects, unreadable background detail, motion blur, action pose, blockbuster cinematic lighting, poster design, collage fragments, multiple surreal events, multiple bright accents

## Style-lock variants

### Variant 1: documentary object portrait
single machine, device, valve, console, or other technical object as the clear subject, subject remains recognizable, restrained room context, one wrong state or anomaly

### Variant 2: evidence room still
one readable room or workstation with a clear main subject, before-or-after-event stillness, one anomaly integrated into the scene, no collage fragments

### Variant 3: environmental thesis
one readable environment with a single subject or system signal, broad but not hollow frame, tension carried by one wrong condition rather than many symbols

## Composition guidance

Choose the clearest placement for the subject. Off-center is useful when it improves readability, but centered or near-centered framing is allowed when the subject needs it. Do not force empty thirds.

## Batch exploration matrix

1. Same prompt, same seed, subject scale changes
2. Same prompt, same aspect ratio, anomaly type changes
3. Same prompt, same aspect ratio, camera distance changes
4. Same prompt, same aspect ratio, palette temperature changes
