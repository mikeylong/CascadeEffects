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

## Prompt template

Use this structure every time:

[subject + setting] + [composition rule] + [color logic] + [single surreal breach] + [lighting/mood] + [render discipline]

## Master prompt

minimal surreal editorial composition, reduced geometric forms, a quiet isolated structure near the far right edge of the frame, vast negative space across most of the image, one dominant environmental field, one saturated accent element used as a semantic signal, exactly one subtle violation of reality, stillness, soft diffuse lighting, clean edges, low detail, high thumbnail readability, asymmetrical balance, contemplative atmosphere

## Negative prompt

high detail, texture, noisy surface, photoreal clutter, many objects, crowded scene, dramatic cinematic lighting, motion blur, action pose, ornate realism, excessive foliage detail, complex sky, center-weighted composition, symmetrical layout, multiple bright accents, text, watermark, logo, ui overlay

## Style-lock variants

### Variant 1: quiet architecture
isolated architecture, simplified silhouette, controlled horizon, sparse environment, subtle reflection

### Variant 2: symbolic landscape
minimal environmental forms, abstracted land-water boundary, one charged natural element, restrained palette

### Variant 3: editorial surreal
editorial illustration sensibility, reduced realism, emotionally restrained, precise visual hierarchy

## Composition bias add-on

subject placed on the outer third, large uninterrupted empty field, off-center focal mass, avoid centered composition

## Batch exploration matrix

1. Same prompt, same seed, aspect ratio changes
2. Same prompt, same aspect ratio, accent element changes
3. Same prompt, same aspect ratio, surreal breach changes
4. Same prompt, same aspect ratio, subject category changes
